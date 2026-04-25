"""Tests for LLM retry behaviour in services/llm.py."""
from unittest.mock import MagicMock, patch

import httpx
import pytest


def _make_response(text: str) -> MagicMock:
    content = MagicMock()
    content.text = text
    response = MagicMock()
    response.content = [content]
    response.usage.input_tokens = 10
    response.usage.output_tokens = 5
    return response


def test_call_llm_succeeds_first_attempt():
    from app.services.llm import call_llm

    mock_resp = _make_response('{"findings": []}')
    with patch("app.services.llm._call_with_retry", return_value=mock_resp):
        result = call_llm(
            system="sys",
            messages=[{"role": "user", "content": "hi"}],
            temperature=0.1,
            max_tokens=100,
            agent_name="test",
        )
    assert result == {"findings": []}


def test_call_llm_retries_on_timeout():
    from app.services.llm import LLMTimeoutError, call_llm

    with patch("app.services.llm._call_with_retry",
               side_effect=httpx.TimeoutException("timed out")):
        with pytest.raises(LLMTimeoutError):
            call_llm(
                system="sys",
                messages=[{"role": "user", "content": "hi"}],
                temperature=0.1,
                max_tokens=100,
                agent_name="test",
            )


def test_call_llm_strips_json_fences():
    from app.services.llm import call_llm

    fenced = '```json\n{"questions": ["Q1"]}\n```'
    mock_resp = _make_response(fenced)
    with patch("app.services.llm._call_with_retry", return_value=mock_resp):
        result = call_llm(
            system="sys",
            messages=[{"role": "user", "content": "hi"}],
            temperature=0.1,
            max_tokens=100,
            agent_name="test",
        )
    assert result == {"questions": ["Q1"]}


def test_call_llm_raises_on_invalid_json():
    import json

    from app.services.llm import call_llm

    mock_resp = _make_response("not json at all")
    with patch("app.services.llm._call_with_retry", return_value=mock_resp):
        with pytest.raises(json.JSONDecodeError):
            call_llm(
                system="sys",
                messages=[{"role": "user", "content": "hi"}],
                temperature=0.1,
                max_tokens=100,
                agent_name="test",
            )
