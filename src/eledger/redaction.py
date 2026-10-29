"""Redaction utilities for eLedger (best-effort, documented patterns)."""
import re, copy

PATTERNS = [
    (re.compile(r"(?i)(api[_-]?key|token|secret|password|passwd|pwd)\s*[:=]\s*\S+"), r"\1=[REDACTED]"),
    (re.compile(r"sk-[A-Za-z0-9]{10,}"), "[REDACTED]"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "[REDACTED]"),
    (re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"), "[REDACTED]"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[REDACTED_EMAIL]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
    (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), "[REDACTED_CARD]"),
]


def _redact_str(s):
    if not isinstance(s, str):
        return s
    out = s
    for pat, repl in PATTERNS:
        out = pat.sub(repl, out)
    return out


def redact(obj, max_depth=20, _depth=0):
    """Return a redacted deep copy. Never mutates input."""
    if _depth > max_depth:
        return obj
    if isinstance(obj, str):
        return _redact_str(obj)
    if isinstance(obj, dict):
        return {k: redact(v, max_depth, _depth + 1) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(x, max_depth, _depth + 1) for x in obj]
    if isinstance(obj, tuple):
        return tuple(redact(x, max_depth, _depth + 1) for x in obj)
    return obj


def redact_text(text):
    return _redact_str(text if isinstance(text, str) else str(text))
