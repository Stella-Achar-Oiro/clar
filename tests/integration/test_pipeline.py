from pathlib import Path
from unittest.mock import patch

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


def test_pipeline_discharge_summary():
    from app.agents.pipeline import run_pipeline

    mock_discharge_findings = {
        "findings": [
            {
                "name": "WBC",
                "value": "14.2 x10^3/uL",
                "unit": "x10^3/uL",
                "reference_range": "4.5-11.0 x10^3/uL",
                "plain_explanation": "Your white blood cell count is elevated, consistent with infection.",
                "confidence": 0.95,
            }
        ]
    }
    mock_discharge_questions = {
        "questions": [
            "When should I finish the antibiotics?",
            "What symptoms mean I need to go back to hospital?",
            "Will my glucose improve once the infection clears?",
            "When will I get my follow-up X-ray?",
            "Should I see a lung specialist?",
        ]
    }

    with patch("app.agents.explain_agent.call_llm", return_value=mock_discharge_findings), \
         patch("app.agents.advisor_agent.call_llm", return_value=mock_discharge_questions):
        result = run_pipeline(FIXTURES / "sample_discharge.txt")

    assert result["error"] is None
    assert result["report_type"] in ("discharge", "lab", "radiology")
    assert len(result["questions"]) == 5
    assert "Mary Johnson" not in result["deid_text"]
    assert "87654321" not in result["deid_text"]


def test_pipeline_aborts_on_empty_file(tmp_path):
    from app.agents.pipeline import run_pipeline

    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")
    with patch("app.agents.deid_agent.deidentify", return_value=("", [], True)):
        result = run_pipeline(empty_file)
    assert result["error"] is not None
