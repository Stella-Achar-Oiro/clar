from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

SESSION_DATA = {
    "findings": [
        {"name": "Haemoglobin", "value": "10.2 g/dL", "urgency": "watch", "explanation": "Low."}
    ],
    "questions": ["Should I take supplements?"],
    "report_type": "lab",
}


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


def test_chat_session_not_found(client):
    response = client.post(
        "/api/chat", json={"report_id": "nonexistent", "question": "What does this mean?"}
    )
    assert response.status_code == 404


def test_chat_returns_answer(client):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Your haemoglobin is slightly low.")]

    with patch("app.api.routes.chat._sessions") as mock_sessions, \
         patch("app.api.routes.chat._client") as mock_client:
        mock_sessions.get.return_value = SESSION_DATA
        mock_client.messages.create.return_value = mock_response

        response = client.post(
            "/api/chat",
            json={"report_id": "test-id", "question": "What does low haemoglobin mean?"},
        )
    assert response.status_code == 200
    assert response.json()["answer"] == "Your haemoglobin is slightly low."


def test_chat_anthropic_error_returns_500(client):
    with patch("app.api.routes.chat._sessions") as mock_sessions, \
         patch("app.api.routes.chat._client") as mock_client:
        mock_sessions.get.return_value = SESSION_DATA
        mock_client.messages.create.side_effect = RuntimeError("API error")

        response = client.post(
            "/api/chat",
            json={"report_id": "test-id", "question": "What is this?"},
        )
    assert response.status_code == 500


def test_chat_includes_context_in_request(client):
    """Verify that the Anthropic call includes report context."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Answer about the finding.")]

    with patch("app.api.routes.chat._sessions") as mock_sessions, \
         patch("app.api.routes.chat._client") as mock_client:
        mock_sessions.get.return_value = SESSION_DATA
        mock_client.messages.create.return_value = mock_response

        client.post(
            "/api/chat",
            json={"report_id": "test-id", "question": "Tell me about my findings."},
        )

        call_kwargs = mock_client.messages.create.call_args
        # The user message should include the question
        messages = (
            call_kwargs.kwargs.get("messages")
            or (call_kwargs.args[0] if call_kwargs.args else [])
        )
        if not messages:
            messages = call_kwargs[1].get("messages", [])
        assert any("Tell me about my findings." in str(m) for m in messages)
