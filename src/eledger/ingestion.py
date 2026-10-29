"""Session ingestion and normalization."""
from .models import SessionMeta, MessageRecord, NormalizedSession, ValidationError


def normalize_session(raw: dict) -> NormalizedSession:
    """Normalize a raw session dict into NormalizedSession. Raises ValidationError on bad input."""
    if not isinstance(raw, dict):
        raise ValidationError("raw session must be dict")
    meta_raw = raw.get("meta") or raw
    meta = SessionMeta(
        session_id=str(meta_raw.get("session_id") or meta_raw.get("id") or ""),
        source=str(meta_raw.get("source", "unknown")),
        started_at=meta_raw.get("started_at"),
        ended_at=meta_raw.get("ended_at"),
        message_count=int(meta_raw.get("message_count", 0) or 0),
    )
    meta.validate()
    msgs = []
    for m in raw.get("messages", []):
        if not isinstance(m, dict):
            raise ValidationError("message must be dict")
        mr = MessageRecord(
            message_id=m.get("id") or m.get("message_id"),
            session_id=str(m.get("session_id") or meta.session_id),
            role=str(m.get("role", "user")),
            content=m.get("content", ""),
            timestamp=m.get("timestamp"),
        )
        mr.validate()
        msgs.append(mr)
    ns = NormalizedSession(meta=meta, messages=msgs, provenance=raw.get("provenance", {}), retrieval_failures=list(raw.get("retrieval_failures", [])))
    ns.validate()
    return ns


def ingest_records(records: list) -> list:
    """Ingest a list of raw session records. Returns list of NormalizedSession; skips malformed with failure tracking."""
    out = []
    for r in records:
        try:
            out.append(normalize_session(r))
        except ValidationError as e:
            # record as a synthetic failed session marker
            out.append({"_error": str(e), "_raw": r})
    return out
