from datetime import datetime, timedelta
from threading import Lock


class SessionStore:
    def __init__(self, ttl_minutes: int) -> None:
        self._ttl = timedelta(minutes=ttl_minutes)
        self._store: dict[str, tuple[dict, datetime]] = {}
        self._lock = Lock()

    def put(self, report_id: str, data: dict) -> None:
        with self._lock:
            self._store[report_id] = (data, datetime.utcnow())

    def get(self, report_id: str) -> dict | None:
        with self._lock:
            entry = self._store.get(report_id)
            if entry is None:
                return None
            data, created_at = entry
            if datetime.utcnow() - created_at > self._ttl:
                del self._store[report_id]
                return None
            return data
