import json
from typing import Any

import httpx
from anthropic import Anthropic
from anthropic.types import MessageParam

from app.config import settings
from app.observability.metrics import LLM_TOKENS


class LLMTimeoutError(Exception):
    pass


_client = Anthropic(
    api_key=settings.anthropic_api_key,
    timeout=httpx.Timeout(30.0),
)

MODEL = "claude-sonnet-4-6"


def call_llm(
    system: str,
    messages: list[dict[str, Any]],
    temperature: float,
    max_tokens: int,
    agent_name: str,
) -> dict[str, Any]:
    # Cast to MessageParam — our dicts always match the expected shape
    typed_messages: list[MessageParam] = [
        {"role": m["role"], "content": m["content"]} for m in messages
    ]
    try:
        response = _client.messages.create(
            model=MODEL,
            system=system,
            messages=typed_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except httpx.TimeoutException as exc:
        raise LLMTimeoutError("LLM call timed out after 30s") from exc

    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    LLM_TOKENS.labels(agent_name=agent_name, direction="input").inc(input_tokens)
    LLM_TOKENS.labels(agent_name=agent_name, direction="output").inc(output_tokens)

    # content[0] is always a TextBlock when no tools are configured
    raw = str(getattr(response.content[0], "text", ""))
    result: dict[str, Any] = json.loads(raw)
    return result
