import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

FIXTURES = Path(__file__).parent.parent / "fixtures"

MOCK_EXPLAIN_RESPONSE = {
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

MOCK_ADVISOR_RESPONSE = {
    "questions": [
        "Could this indicate anaemia?",
        "Should I take iron supplements?",
        "What foods would help?",
        "How soon should I retest?",
        "Should I see a specialist?",
    ]
}


def test_pipeline_runs_end_to_end():
    from app.agents.pipeline import run_pipeline

    with patch("app.agents.explain_agent.call_llm", return_value=MOCK_EXPLAIN_RESPONSE), \
         patch("app.agents.advisor_agent.call_llm", return_value=MOCK_ADVISOR_RESPONSE):
        result = run_pipeline(FIXTURES / "sample_cbc.txt")

    assert result["report_type"] == "lab"
    assert len(result["explanations"]) >= 1
    assert len(result["flagged"]) >= 1
    assert len(result["questions"]) == 5
    assert result["error"] is None


def test_pipeline_deid_removes_pii():
    from app.agents.pipeline import run_pipeline

    with patch("app.agents.explain_agent.call_llm", return_value=MOCK_EXPLAIN_RESPONSE), \
         patch("app.agents.advisor_agent.call_llm", return_value=MOCK_ADVISOR_RESPONSE):
        result = run_pipeline(FIXTURES / "sample_cbc.txt")

    assert "John Smith" not in result["deid_text"]
    assert "12345678" not in result["deid_text"]


def test_pipeline_aborts_on_empty_file(tmp_path):
    from app.agents.pipeline import run_pipeline

    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")
    result = run_pipeline(empty_file)
    assert result["error"] is not None
