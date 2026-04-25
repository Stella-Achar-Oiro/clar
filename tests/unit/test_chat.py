from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

CHAT_PAYLOAD = {
    "report_id": "test-id",
    "question": "What does low haemoglobin mean?",
    "report_type": "lab",
    "findings": [
        {
            "name": "Haemoglobin",
            "value": "10.2 g/dL",
            "reference_range": "12.0-16.0 g/dL",
            "urgency": "watch",
            "explanation": "Your haemoglobin is slightly below the normal range.",
        }
    ],
    "questions": ["Should I take supplements?"],
}


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


def test_chat_returns_answer(client):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Your haemoglobin is slightly low.")]

    with patch("app.api.routes.chat._client") as mock_client:
        mock_client.messages.create.return_value = mock_response
        response = client.post("/api/chat", json=CHAT_PAYLOAD)

    assert response.status_code == 200
    assert response.json()["answer"] == "Your haemoglobin is slightly low."


def test_chat_anthropic_error_returns_500(client):
    with patch("app.api.routes.chat._client") as mock_client:
        mock_client.messages.create.side_effect = RuntimeError("API error")
        response = client.post("/api/chat", json=CHAT_PAYLOAD)

    assert response.status_code == 500


def test_chat_includes_context_in_request(client):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Answer about the finding.")]

    with patch("app.api.routes.chat._client") as mock_client:
        mock_client.messages.create.return_value = mock_response
        client.post("/api/chat", json=CHAT_PAYLOAD)

        call_kwargs = mock_client.messages.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages", [])
        content = " ".join(str(m) for m in messages)
        assert "What does low haemoglobin mean?" in content
        assert "Haemoglobin" in content


def test_chat_empty_findings_still_responds(client):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="No findings were provided.")]

    payload = {**CHAT_PAYLOAD, "findings": [], "questions": []}
    with patch("app.api.routes.chat._client") as mock_client:
        mock_client.messages.create.return_value = mock_response
        response = client.post("/api/chat", json=payload)

    assert response.status_code == 200
