import pytest
from unittest.mock import patch
from app.agents.advisor_agent import run_advisor_agent
from app.models.report import CLARState


def _make_state(flagged: list[dict], report_type: str = "lab") -> CLARState:
    return CLARState(
        raw_text="", deid_text="", report_type=report_type,
        findings=[], explanations=[], flagged=flagged,
        questions=[], deid_entities=[], error=None,
    )


MOCK_QUESTIONS_RESPONSE = {
    "questions": [
        "Could the low haemoglobin and MCV together indicate iron-deficiency anaemia?",
        "Should I start iron supplements or wait for more tests?",
        "Is there anything in my diet that could be causing the low haemoglobin?",
        "How long will it take for my haemoglobin to return to normal with treatment?",
        "Should I reduce physical activity until my levels improve?",
    ]
}

FLAGGED = [
    {"name": "Haemoglobin", "value": "10.2 g/dL", "reference_range": "12.0-16.0 g/dL",
     "urgency": "watch", "urgency_reason": "Below normal range", "plain_explanation": "Low."}
]


def test_advisor_returns_exactly_5_questions():
    state = _make_state(FLAGGED)
    with patch("app.agents.advisor_agent.call_llm", return_value=MOCK_QUESTIONS_RESPONSE):
        result = run_advisor_agent(state)
    assert len(result["questions"]) == 5


def test_advisor_questions_are_strings():
    state = _make_state(FLAGGED)
    with patch("app.agents.advisor_agent.call_llm", return_value=MOCK_QUESTIONS_RESPONSE):
        result = run_advisor_agent(state)
    assert all(isinstance(q, str) for q in result["questions"])


def test_advisor_no_error_on_success():
    state = _make_state(FLAGGED)
    with patch("app.agents.advisor_agent.call_llm", return_value=MOCK_QUESTIONS_RESPONSE):
        result = run_advisor_agent(state)
    assert result["error"] is None


def test_advisor_sets_error_on_llm_failure():
    state = _make_state(FLAGGED)
    with patch("app.agents.advisor_agent.call_llm", side_effect=Exception("timeout")):
        result = run_advisor_agent(state)
    assert result["error"] is not None


def test_advisor_preserves_flagged_findings():
    state = _make_state(FLAGGED)
    with patch("app.agents.advisor_agent.call_llm", return_value=MOCK_QUESTIONS_RESPONSE):
        result = run_advisor_agent(state)
    assert result["flagged"] == FLAGGED
