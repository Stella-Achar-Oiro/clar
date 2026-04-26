import json
from typing import Any

import httpx
from anthropic import Anthropic, APIStatusError
from anthropic.types import MessageParam
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings
from app.observability.metrics import LLM_TOKENS


class LLMTimeoutError(Exception):
    pass


_client = Anthropic(
    api_key=settings.anthropic_api_key,
    timeout=httpx.Timeout(30.0),
)

MODEL = "claude-sonnet-4-6"

# Retry on transient server errors (5xx) and rate limits (529), up to 3 attempts
# with exponential backoff: 2s, 4s
_RETRYABLE = (httpx.TimeoutException, APIStatusError)


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, APIStatusError):
        return exc.status_code in (429, 500, 502, 503, 529)
    return False


@retry(
    retry=retry_if_exception_type(_RETRYABLE),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    reraise=True,
)
def _call_with_retry(
    typed_messages: list[MessageParam],
    system: str,
    temperature: float,
    max_tokens: int,
) -> Any:
    return _client.messages.create(
        model=MODEL,
        system=system,
        messages=typed_messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def call_llm(
    system: str,
    messages: list[dict[str, Any]],
    temperature: float,
    max_tokens: int,
    agent_name: str,
) -> dict[str, Any]:
    typed_messages: list[MessageParam] = [
        {"role": m["role"], "content": m["content"]} for m in messages
    ]
    try:
        response = _call_with_retry(typed_messages, system, temperature, max_tokens)
    except httpx.TimeoutException as exc:
        raise LLMTimeoutError("LLM call timed out after 30s") from exc
    except APIStatusError as exc:
        logger.error("llm_api_error", status=exc.status_code, agent=agent_name)
        raise

    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    LLM_TOKENS.labels(agent_name=agent_name, direction="input").inc(input_tokens)
    LLM_TOKENS.labels(agent_name=agent_name, direction="output").inc(output_tokens)

    raw = str(getattr(response.content[0], "text", ""))
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0]
    try:
        result: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        # Response was likely truncated — try to salvage a partial findings array
        logger.warning("llm_json_truncated", agent=agent_name, raw_length=len(raw))
        result = _repair_truncated_json(raw)
    return result


def _repair_truncated_json(raw: str) -> dict[str, Any]:
    """Best-effort recovery for truncated LLM JSON responses."""
    # For findings responses: extract complete objects before the truncation point
    import re
    findings = re.findall(r'\{[^{}]*"name"[^{}]*\}', raw, re.DOTALL)
    if findings:
        complete = []
        for f in findings:
            try:
                complete.append(json.loads(f))
            except json.JSONDecodeError:
                pass
        if complete:
            return {"findings": complete}
    # For other shapes (urgency, questions): return safe empty defaults
    if '"urgency"' in raw:
        return {"urgency": "watch", "urgency_reason": "Could not fully parse response."}
    if '"questions"' in raw:
        return {"questions": []}
    return {}
