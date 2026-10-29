"""Redaction tests."""
from eledger.redaction import redact, redact_text

def test_redact_secret():
    d = {"token": "sk-abcdefghij1234567890", "msg": "password=hunter2"}
    r = redact(d)
    assert "[REDACTED]" in str(r) or "REDACTED" in str(r)
    assert r["token"] == "[REDACTED]" or "REDACTED" in r["token"]
    # non-sensitive preserved
    d2 = {"count": 5, "name": "alice"}
    assert redact(d2) == d2

def test_redact_nested():
    d = {"a": {"b": [{"c": "ghp_" + "a"*30}]}}
    r = redact(d)
    assert "REDACTED" in str(r)

def test_redact_malformed_safe():
    assert redact(None) is None
    assert redact(42) == 42
    assert redact("plain") == "plain"

def test_redact_no_mutation():
    d = {"x": "sk-abcdefghij1234567890"}
    orig = {"x": "sk-abcdefghij1234567890"}
    redact(d)
    assert d == orig

def test_redact_text():
    assert "REDACTED" in redact_text("email foo@bar.com here")
