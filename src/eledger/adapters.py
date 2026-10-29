"""Session reader interface and synthetic adapter (read-only)."""
from typing import Protocol, List, Dict, Any
from .models import ValidationError


class SessionReader(Protocol):
    def list_sessions(self, window_start: str, window_end: str) -> List[Dict[str, Any]]:
        ...
    def read_session(self, session_id: str) -> Dict[str, Any]:
        ...
    def is_readonly(self) -> bool:
        ...


class SyntheticSessionReader:
    """In-memory read-only adapter for tests. No real session access."""

    def __init__(self, records: List[Dict[str, Any]]):
        self._records = {r["meta"]["session_id"]: r for r in records}
        self._readonly = True

    def list_sessions(self, window_start, window_end):
        return list(self._records.keys())

    def read_session(self, session_id):
        if session_id not in self._records:
            raise KeyError(f"unknown session: {session_id}")
        return self._records[session_id]

    def is_readonly(self):
        return self._readonly

    def read_all(self):
        return list(self._records.values())


def validate_reader(reader) -> bool:
    if not hasattr(reader, "list_sessions") or not hasattr(reader, "read_session") or not hasattr(reader, "is_readonly"):
        return False
    if not reader.is_readonly():
        return False
    return True
