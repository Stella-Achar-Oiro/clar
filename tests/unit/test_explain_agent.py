import pytest
from unittest.mock import patch
from app.agents.explain_agent import run_explain_agent
from app.models.report import CLARState


def _make_state(deid_text: str = "", report_type: str = "lab") -> CLARState:
    return CLARState(
        raw_text="",
        deid_text=deid_text,
        report_type=report_type,
        findings=[],
        explanations=[],
        flagged=[],
        questions=[],
        deid_entities=[],
        error=None,
    )


MOCK_LLM_RESPONSE = {
    "findings": [
        {
            "name": "Haemoglobin",
            "value": "10.2 g/dL",
            "unit": "g/dL",
            "reference_range": "12.0-16.0 g/dL",
            "plain_explanation": "Your haemoglobin is slightly below the normal range.",
            "confidence": 0.95,
        }
    ]
}


def test_explain_agent_returns_findings():
    with patch("app.agents.explain_agent.call_llm", return_value=MOCK_LLM_RESPONSE):
        state = _make_state(deid_text="Haemoglobin: 10.2 g/dL (Reference: 12.0-16.0 g/dL)")
        result = run_explain_agent(state)
    assert len(result["explanations"]) == 1
    assert result["explanations"][0]["name"] == "Haemoglobin"


def test_explain_agent_no_error_on_success():
    with patch("app.agents.explain_agent.call_llm", return_value=MOCK_LLM_RESPONSE):
        state = _make_state(deid_text="Haemoglobin: 10.2 g/dL")
        result = run_explain_agent(state)
    assert result["error"] is None


def test_explain_agent_sets_error_on_llm_failure():
    with patch("app.agents.explain_agent.call_llm", side_effect=Exception("LLM timeout")):
        state = _make_state(deid_text="Haemoglobin: 10.2 g/dL")
        result = run_explain_agent(state)
    assert result["error"] is not None


def test_explain_agent_preserves_existing_state_fields():
    with patch("app.agents.explain_agent.call_llm", return_value=MOCK_LLM_RESPONSE):
        state = _make_state(deid_text="Haemoglobin: 10.2 g/dL", report_type="lab")
        state["deid_entities"] = [{"type": "PERSON", "count": 1}]
        result = run_explain_agent(state)
    assert result["deid_entities"] == [{"type": "PERSON", "count": 1}]
    assert result["report_type"] == "lab"
