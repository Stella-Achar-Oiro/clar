from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

FIXTURES = Path(__file__).parent.parent / "fixtures"

MOCK_PIPELINE_STATE = {
    "raw_text": "",
    "deid_text": "Haemoglobin: 10.2 g/dL",
    "report_type": "lab",
    "findings": [],
    "explanations": [],
    "flagged": [
        {
            "name": "Haemoglobin",
            "value": "10.2 g/dL",
            "reference_range": "12.0-16.0 g/dL",
            "urgency": "watch",
            "urgency_reason": "Below normal",
            "plain_explanation": "Low haemoglobin.",
        }
    ],
    "questions": ["Should I take iron supplements?", "Q2", "Q3", "Q4", "Q5"],
    "deid_entities": [{"type": "PERSON", "count": 1}],
    "error": None,
}


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


def test_upload_valid_txt(client):
    with patch("app.api.routes.upload.run_pipeline", return_value=MOCK_PIPELINE_STATE):
        response = client.post(
            "/api/upload",
            files={"file": ("report.txt", b"Haemoglobin: 10.2 g/dL", "text/plain")},
        )
    assert response.status_code == 200
    data = response.json()
    assert "report_id" in data
    assert data["report_type"] == "lab"
    assert len(data["findings"]) == 1


def test_upload_unsupported_extension(client):
    response = client.post(
        "/api/upload",
        files={"file": ("report.doc", b"content", "application/msword")},
    )
    assert response.status_code == 415


def test_upload_file_too_large(client):
    big_content = b"x" * (11 * 1024 * 1024)  # 11 MB
    response = client.post(
        "/api/upload",
        files={"file": ("report.txt", big_content, "text/plain")},
    )
    assert response.status_code == 413


def test_upload_deid_failed_returns_422(client):
    failed_state = {**MOCK_PIPELINE_STATE, "error": "deid_failed"}
    with patch("app.api.routes.upload.run_pipeline", return_value=failed_state):
        response = client.post(
            "/api/upload",
            files={"file": ("report.txt", b"content", "text/plain")},
        )
    assert response.status_code == 422


def test_upload_verdict_urgent(client):
    urgent_state = {
        **MOCK_PIPELINE_STATE,
        "flagged": [
            {
                "name": "Haemoglobin",
                "value": "4.0 g/dL",
                "reference_range": "12.0-16.0 g/dL",
                "urgency": "urgent",
                "urgency_reason": "Critically low",
                "plain_explanation": "Very low.",
            }
        ],
    }
    with patch("app.api.routes.upload.run_pipeline", return_value=urgent_state):
        response = client.post(
            "/api/upload",
            files={"file": ("report.txt", b"content", "text/plain")},
        )
    assert response.status_code == 200
    assert response.json()["verdict"]["level"] == "urgent"


def test_upload_verdict_normal(client):
    normal_state = {
        **MOCK_PIPELINE_STATE,
        "flagged": [],
    }
    with patch("app.api.routes.upload.run_pipeline", return_value=normal_state):
        response = client.post(
            "/api/upload",
            files={"file": ("report.txt", b"content", "text/plain")},
        )
    assert response.status_code == 200
    assert response.json()["verdict"]["level"] == "normal"


def test_upload_pipeline_exception_returns_500(client):
    with patch("app.api.routes.upload.run_pipeline", side_effect=RuntimeError("pipeline boom")):
        response = client.post(
            "/api/upload",
            files={"file": ("report.txt", b"content", "text/plain")},
        )
    assert response.status_code == 500


def test_upload_deid_entities_counted(client):
    state = {
        **MOCK_PIPELINE_STATE,
        "deid_entities": [{"type": "PERSON", "count": 2}, {"type": "DATE", "count": 3}],
    }
    with patch("app.api.routes.upload.run_pipeline", return_value=state):
        response = client.post(
            "/api/upload",
            files={"file": ("report.txt", b"content", "text/plain")},
        )
    assert response.status_code == 200
    assert response.json()["deid_entities_removed"] == 5
