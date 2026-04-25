from collections.abc import Iterator

from anthropic import Anthropic
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

from app.config import settings
from app.models.report import ChatRequest, ChatResponse

router = APIRouter(prefix="/api")
_client = Anthropic(api_key=settings.anthropic_api_key)

_CHAT_SYSTEM = (
    "You are CLAR, a medical report assistant. Answer questions about a patient's"
    " de-identified medical report findings. Be clear, helpful, and non-alarmist."
    " Do not diagnose. Do not recommend specific treatments."
    " Suggest consulting their doctor for medical decisions."
    " FORMATTING RULES: No emojis. Use plain markdown only — bold (**word**) and"
    " bullet lists are fine. Never use broken or unclosed markdown syntax."
    " If the findings list in the context is empty, say so in one plain sentence."
)


def _build_context(request: ChatRequest) -> str:
    findings_text = "\n".join(
        f"- {f.name}: {f.value} ({f.urgency.upper()}) — {f.explanation}"
        for f in request.findings
    ) or "No findings provided."
    questions_text = "\n".join(f"- {q}" for q in request.questions) or "None."
    return (
        f"Report type: {request.report_type or 'unknown'}\n\n"
        f"Findings:\n{findings_text}\n\n"
        f"Suggested questions:\n{questions_text}"
    )


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    context = _build_context(request)
    try:
        response = _client.messages.create(
            model="claude-sonnet-4-6",
            system=_CHAT_SYSTEM,
            messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {request.question}"}],  # noqa: E501
            temperature=0.3,
            max_tokens=500,
        )
        answer = str(getattr(response.content[0], "text", ""))
        logger.debug("chat_answered", report_id=request.report_id)
        return ChatResponse(answer=answer)
    except Exception as exc:
        logger.error("chat_failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Chat is temporarily unavailable.")


@router.post("/chat/stream")
def chat_stream(request: ChatRequest) -> StreamingResponse:
    context = _build_context(request)

    def generate() -> Iterator[str]:
        try:
            with _client.messages.stream(
                model="claude-sonnet-4-6",
                system=_CHAT_SYSTEM,
                messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {request.question}"}],  # noqa: E501
                temperature=0.3,
                max_tokens=500,
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {text}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:
            logger.error("chat_stream_failed", error=str(exc))
            yield "data: [ERROR]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
