import time
import uuid
from pathlib import Path
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.agents.pipeline import run_pipeline
from app.models.report import ReportResult, Verdict, Finding
from app.services.session import get_shared_store
from app.config import settings
from app.observability.metrics import REQUESTS_TOTAL, PIPELINE_DURATION, DEID_ENTITIES_TOTAL, ERRORS_TOTAL
from loguru import logger

router = APIRouter(prefix="/api")

_sessions = get_shared_store()

_ALLOWED_EXTENSIONS = {".pdf", ".txt"}


@router.post("/upload", response_model=ReportResult)
async def upload_report(file: UploadFile = File(...)) -> ReportResult:
    request_id = str(uuid.uuid4())
    logger.info("upload_received", filename=file.filename, request_id=request_id)

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        ERRORS_TOTAL.labels(error_type="unsupported_file_type").inc()
        raise HTTPException(status_code=415, detail="Only PDF and plain text files are supported")

    content = await file.read()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        ERRORS_TOTAL.labels(error_type="file_too_large").inc()
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit")

    start = time.time()
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            state = run_pipeline(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)

        if state.get("error") == "deid_failed":
            ERRORS_TOTAL.labels(error_type="deid_failed").inc()
            raise HTTPException(status_code=422, detail="Could not safely process this document. Please try again.")

        duration_ms = int((time.time() - start) * 1000)
        deid_count = sum(e["count"] for e in state.get("deid_entities", []))
        DEID_ENTITIES_TOTAL.inc(deid_count)

        report_id = str(uuid.uuid4())
        findings = [
            Finding(
                name=f["name"],
                value=f["value"],
                reference_range=f.get("reference_range", ""),
                urgency=f["urgency"],
                urgency_reason=f["urgency_reason"],
                explanation=f.get("plain_explanation", ""),
            )
            for f in state["flagged"]
        ]

        urgent_count = sum(1 for f in findings if f.urgency == "urgent")
        watch_count = sum(1 for f in findings if f.urgency == "watch")
        if urgent_count > 0:
            verdict_level = "urgent"
            verdict_summary = f"{urgent_count} finding(s) require prompt attention"
        elif watch_count > 0:
            verdict_level = "watch"
            verdict_summary = f"{watch_count} finding(s) flagged for attention"
        else:
            verdict_level = "normal"
            verdict_summary = "All findings are within normal range"

        _sessions.put(report_id, {
            "findings": [f.model_dump() for f in findings],
            "questions": state["questions"],
            "report_type": state["report_type"],
        })

        REQUESTS_TOTAL.labels(report_type=state["report_type"], status="success").inc()
        PIPELINE_DURATION.observe(time.time() - start)

        return ReportResult(
            report_id=report_id,
            report_type=state["report_type"],
            verdict=Verdict(level=verdict_level, summary=verdict_summary),
            findings=findings,
            questions=state["questions"],
            processing_time_ms=duration_ms,
            deid_entities_removed=deid_count,
        )

    except HTTPException:
        raise
    except Exception as exc:
        ERRORS_TOTAL.labels(error_type="pipeline_error").inc()
        logger.error("upload_failed", error=str(exc), request_id=request_id)
        raise HTTPException(status_code=500, detail=str(exc))
