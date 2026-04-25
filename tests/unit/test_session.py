import time

from app.services.session import SessionStore


def test_store_and_retrieve():
    store = SessionStore(ttl_minutes=1)
    store.put("abc", {"findings": [], "questions": [], "report_type": "lab"})
    data = store.get("abc")
    assert data is not None
    assert data["report_type"] == "lab"


def test_missing_key_returns_none():
    store = SessionStore(ttl_minutes=1)
    assert store.get("nonexistent") is None


def test_expired_key_returns_none():
    store = SessionStore(ttl_minutes=0)  # 0 minutes = immediate expiry
    store.put("abc", {"findings": [], "questions": [], "report_type": "lab"})
    time.sleep(0.01)
    assert store.get("abc") is None
