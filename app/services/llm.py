import json
import httpx
from anthropic import Anthropic
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
    messages: list[dict],
    temperature: float,
    max_tokens: int,
    agent_name: str,
) -> dict:
    try:
        response = _client.messages.create(
            model=MODEL,
            system=system,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except httpx.TimeoutException as exc:
        raise LLMTimeoutError("LLM call timed out after 30s") from exc

    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    LLM_TOKENS.labels(agent_name=agent_name, direction="input").inc(input_tokens)
    LLM_TOKENS.labels(agent_name=agent_name, direction="output").inc(output_tokens)

    raw = response.content[0].text
    return json.loads(raw)
