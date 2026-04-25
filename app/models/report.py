from typing import Any, TypedDict

from pydantic import BaseModel


class CLARState(TypedDict):
    raw_text: str
    deid_text: str
    report_type: str
    findings: list[dict[str, Any]]
    explanations: list[dict[str, Any]]
    flagged: list[dict[str, Any]]
    questions: list[str]
    deid_entities: list[dict[str, Any]]
    error: str | None


class Finding(BaseModel):
    name: str
    value: str
    reference_range: str
    urgency: str
    urgency_reason: str
    explanation: str


class Verdict(BaseModel):
    level: str
    summary: str


class ReportResult(BaseModel):
    report_id: str
    report_type: str
    verdict: Verdict
    findings: list[Finding]
    questions: list[str]
    processing_time_ms: int
    deid_entities_removed: int


class ChatFinding(BaseModel):
    name: str
    value: str
    reference_range: str
    urgency: str
    explanation: str


class ChatRequest(BaseModel):
    report_id: str
    question: str
    report_type: str = ""
    findings: list[ChatFinding] = []
    questions: list[str] = []


class ChatResponse(BaseModel):
    answer: str
