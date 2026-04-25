from unittest.mock import patch

from app.agents.flag_agent import classify_numeric, run_flag_agent
from app.models.report import CLARState


def _make_state(explanations: list[dict]) -> CLARState:
    return CLARState(
        raw_text="", deid_text="", report_type="lab",
        findings=[], explanations=explanations, flagged=[],
        questions=[], deid_entities=[], error=None,
    )


def test_classify_numeric_below_range_is_watch():
    urgency, reason = classify_numeric(value=10.2, low=12.0, high=16.0)
    assert urgency == "watch"
    assert "below" in reason.lower()


def test_classify_numeric_within_range_is_normal():
    urgency, reason = classify_numeric(value=6.2, low=4.5, high=11.0)
    assert urgency == "normal"


def test_classify_numeric_critically_low_is_urgent():
    urgency, reason = classify_numeric(value=5.0, low=12.0, high=16.0)
    assert urgency == "urgent"


def test_classify_numeric_above_range_is_watch():
    urgency, reason = classify_numeric(value=12.0, low=4.5, high=11.0)
    assert urgency == "watch"


def test_flag_agent_uses_rules_for_numeric_range():
    explanations = [
        {
            "name": "Haemoglobin",
            "value": "10.2 g/dL",
            "unit": "g/dL",
            "reference_range": "12.0-16.0 g/dL",
            "plain_explanation": "Slightly low.",
            "confidence": 0.95,
        }
    ]
    state = _make_state(explanations)
    with patch("app.agents.flag_agent.call_llm") as mock_llm:
        result = run_flag_agent(state)
    mock_llm.assert_not_called()
    assert result["flagged"][0]["urgency"] == "watch"


def test_flag_agent_uses_llm_for_qualitative_finding():
    explanations = [
        {
            "name": "Right Lower Lobe Consolidation",
            "value": "Mild",
            "unit": "",
            "reference_range": "No consolidation expected",
            "plain_explanation": "Area of lung looks denser than normal.",
            "confidence": 0.88,
        }
    ]
    state = _make_state(explanations)
    mock_response = {"urgency": "watch", "urgency_reason": "Consolidation present, monitor closely"}
    with patch("app.agents.flag_agent.call_llm", return_value=mock_response):
        result = run_flag_agent(state)
    assert result["flagged"][0]["urgency"] in ("normal", "watch", "urgent")


def test_flag_agent_returns_all_findings():
    explanations = [
        {
            "name": "A", "value": "5.0", "unit": "",
            "reference_range": "4.0-6.0", "plain_explanation": "x", "confidence": 0.9,
        },
        {
            "name": "B", "value": "2.0", "unit": "",
            "reference_range": "4.0-6.0", "plain_explanation": "x", "confidence": 0.9,
        },
    ]
    state = _make_state(explanations)
    result = run_flag_agent(state)
    assert len(result["flagged"]) == 2
