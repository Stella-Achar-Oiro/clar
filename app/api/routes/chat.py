from collections.abc import Iterator

from anthropic import Anthropic
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

from app.config import settings
from app.models.report import ChatRequest, ChatResponse
from app.services.session import get_shared_store

router = APIRouter(prefix="/api")
_client = Anthropic(api_key=settings.anthropic_api_key)
_sessions = get_shared_store()

_CHAT_SYSTEM = (
    "You are CLAR, a medical report assistant. Answer questions about a patient's"
    " de-identified medical report findings. Be clear, helpful, and non-alarmist."
    " Do not diagnose. Do not recommend specific treatments."
    " Suggest consulting their doctor for medical decisions."
)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    session = _sessions.get(request.report_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Report session not found or expired. Please upload your report again.",
        )

    context = _build_context(session)

    try:
        response = _client.messages.create(
            model="claude-sonnet-4-6",
            system=_CHAT_SYSTEM,
            messages=[
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {request.question}"},
            ],
            temperature=0.3,
            max_tokens=500,
        )
        # content[0] is always a TextBlock when no tools are configured
        answer = str(getattr(response.content[0], "text", ""))
        logger.debug("chat_answered", report_id=request.report_id)
        return ChatResponse(answer=answer)
    except Exception as exc:
        logger.error("chat_failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Chat is temporarily unavailable.")


def _build_context(session: dict[str, object]) -> str:
    return f"""Report type: {session['report_type']}

Findings:
{chr(10).join(
    f"- {f['name']}: {f['value']} ({f['urgency'].upper()}) — {f['explanation']}"
    for f in session['findings']
)}

Suggested questions:
{chr(10).join(f"- {q}" for q in session['questions'])}"""


@router.post("/chat/stream")
def chat_stream(request: ChatRequest) -> StreamingResponse:
    session = _sessions.get(request.report_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Report session not found or expired. Please upload your report again.",
        )

    context = _build_context(session)

    def generate() -> Iterator[str]:
        try:
            with _client.messages.stream(
                model="claude-sonnet-4-6",
                system=_CHAT_SYSTEM,
                messages=[
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {request.question}",
                    },
                ],
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
