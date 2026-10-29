"""Hermes state.db read-only adapter."""
import sqlite3
from typing import List, Dict, Any

SUPPORTED_SCHEMA_VERSION = 23

REQUIRED_SESSIONS_COLS = {"id", "source", "started_at", "ended_at", "message_count", "parent_session_id", "archived", "pinned"}
REQUIRED_MESSAGES_COLS = {"id", "session_id", "role", "content", "timestamp", "active", "compacted"}


class SchemaError(Exception):
    pass


class HermesStateDbReader:
    def __init__(self, db_path: str, supported_version: int = SUPPORTED_SCHEMA_VERSION):
        self.db_path = db_path
        self.supported_version = supported_version
        self._conn = None

    def _connect(self):
        if self._conn is not None:
            return self._conn
        uri = f"file:{self.db_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.execute("PRAGMA query_only = ON")
        self._conn = conn
        self._validate_schema()
        return conn

    def _validate_schema(self):
        conn = self._conn
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "sessions" not in tables or "messages" not in tables:
            raise SchemaError("missing sessions or messages table")
        if "schema_version" in tables:
            ver = conn.execute("SELECT version FROM schema_version").fetchone()
            if not ver or ver[0] != self.supported_version:
                raise SchemaError(f"unsupported schema version: {ver[0] if ver else None}")
        sess_cols = {r[1] for r in conn.execute("PRAGMA table_info(sessions)").fetchall()}
        msg_cols = {r[1] for r in conn.execute("PRAGMA table_info(messages)").fetchall()}
        if not REQUIRED_SESSIONS_COLS.issubset(sess_cols):
            raise SchemaError(f"sessions missing columns: {REQUIRED_SESSIONS_COLS - sess_cols}")
        if not REQUIRED_MESSAGES_COLS.issubset(msg_cols):
            raise SchemaError(f"messages missing columns: {REQUIRED_MESSAGES_COLS - msg_cols}")
        # FK check
        fks = conn.execute("PRAGMA foreign_key_list(messages)").fetchall()
        if not any(fk[2] == "sessions" and fk[3] == "session_id" and fk[4] == "id" for fk in fks):
            raise SchemaError("messages.session_id -> sessions.id FK missing")

    def is_readonly(self) -> bool:
        return True

    def list_sessions(self, window_start=None, window_end=None) -> List[str]:
        conn = self._connect()
        rows = conn.execute("SELECT id FROM sessions ORDER BY id").fetchall()
        return [r[0] for r in rows]

    def read_session(self, session_id: str) -> Dict[str, Any]:
        conn = self._connect()
        srow = conn.execute(
            "SELECT id, source, started_at, ended_at, message_count, parent_session_id, archived, pinned FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if not srow:
            raise KeyError(f"unknown session: {session_id}")
        sid, source, started_at, ended_at, mc, parent, archived, pinned = srow
        msgs = conn.execute(
            "SELECT id, role, content, timestamp, active, compacted FROM messages WHERE session_id = ? AND active = 1 ORDER BY timestamp, id",
            (session_id,),
        ).fetchall()
        messages = []
        for mid, role, content, ts, active, compacted in msgs:
            messages.append({
                "id": mid,
                "session_id": sid,
                "role": role,
                "content": content,
                "timestamp": ts,
                "active": bool(active),
                "compacted": bool(compacted),
            })
        return {
            "meta": {
                "session_id": sid,
                "source": source or "hermes",
                "started_at": started_at,
                "ended_at": ended_at,
                "message_count": mc if mc is not None else len(messages),
                "parent_session_id": parent,
                "archived": bool(archived) if archived is not None else False,
                "pinned": bool(pinned) if pinned is not None else False,
            },
            "messages": messages,
            "provenance": {"source": "hermes-state-db", "db": self.db_path},
            "retrieval_failures": [],
        }

    def read_all(self) -> List[Dict[str, Any]]:
        return [self.read_session(s) for s in self.list_sessions()]

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None
