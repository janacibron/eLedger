"""Read-only HTTP request dump reader."""
import json, os
from pathlib import Path
from .redaction import redact

MAX_FILE_BYTES = 5 * 1024 * 1024
REQUIRED_TOP = {"timestamp", "session_id", "request", "error"}
REQUIRED_REQUEST = {"method", "url", "headers", "body"}
REQUIRED_ERROR = {"type", "message", "status_code", "body", "response_status", "response_text"}


class RequestDumpError(Exception):
    pass


class RequestDumpReader:
    def __init__(self, source_path: str):
        self.source_path = source_path

    def is_readonly(self) -> bool:
        return True

    def _load(self, path: str) -> dict:
        p = Path(path)
        if not p.is_file():
            raise RequestDumpError(f"not a file: {path}")
        if p.stat().st_size > MAX_FILE_BYTES:
            raise RequestDumpError("file too large")
        # symlink guard
        if p.is_symlink():
            raise RequestDumpError("symlink not allowed")
        try:
            raw = p.read_text(encoding="utf-8")
        except Exception as e:
            raise RequestDumpError(f"read failed: {e}")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise RequestDumpError(f"invalid json: {e}")
        if not isinstance(data, dict):
            raise RequestDumpError("top-level must be object")
        if not REQUIRED_TOP.issubset(data.keys()):
            raise RequestDumpError(f"missing top-level keys: {REQUIRED_TOP - set(data.keys())}")
        req = data["request"]
        err = data["error"]
        if not isinstance(req, dict) or not REQUIRED_REQUEST.issubset(req.keys()):
            raise RequestDumpError("invalid request object")
        if not isinstance(err, dict) or not REQUIRED_ERROR.issubset(err.keys()):
            raise RequestDumpError("invalid error object")
        if not isinstance(req["headers"], dict):
            raise RequestDumpError("headers must be object")
        if not isinstance(req["body"], dict):
            raise RequestDumpError("request body must be object")
        # messages
        msgs = req["body"].get("messages")
        if msgs is not None and not isinstance(msgs, list):
            raise RequestDumpError("messages must be list")
        return data

    def list_sessions(self, window_start=None, window_end=None):
        p = Path(self.source_path)
        if p.is_dir():
            return sorted(str(x) for x in p.glob("request_dump_*.json"))
        if p.is_file():
            return [str(p)]
        raise RequestDumpError("source not found")

    def read_session(self, file_path: str) -> dict:
        data = self._load(file_path)
        sid = str(data.get("session_id", ""))
        ts = data.get("timestamp")
        req = data["request"]
        body = req["body"]
        raw_msgs = body.get("messages") or []
        messages = []
        for i, m in enumerate(raw_msgs):
            if not isinstance(m, dict):
                continue
            messages.append({
                "message_id": i,
                "session_id": sid,
                "role": str(m.get("role", "unknown")),
                "content": m.get("content"),
                "timestamp": ts,
            })
        out = {
            "meta": {
                "session_id": sid,
                "source": "http-request-dump",
                "started_at": ts,
                "ended_at": ts,
                "message_count": len(messages),
                "model": body.get("model"),
            },
            "messages": messages,
            "provenance": {
                "source": "request-dump",
                "file": str(Path(file_path).name),
                "timestamp": ts,
                "reason": data.get("reason"),
                "error_type": data["error"].get("type"),
                "status_code": data["error"].get("status_code"),
                "response_status": data["error"].get("response_status"),
            },
            "retrieval_failures": [],
        }
        return redact(out)
