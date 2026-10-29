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


def test_redact_patterns():
    from eledger.redaction import redact_text
    cases = [
        ("sk-abcdefghijklmnopqrstuvwxyz", "[REDACTED]"),
        ("ghp_" + "a"*30, "[REDACTED]"),
        ("token = abc123xyz", "REDACTED"),
        ("password=hunter2", "REDACTED"),
        ("email foo@bar.com here", "REDACTED_EMAIL"),
        ("ssn 123-45-6789", "REDACTED_SSN"),
    ]
    for inp, marker in cases:
        out = redact_text(inp)
        assert marker in out, f"{marker} not in {out!r} for {inp!r}"

def test_redact_no_false_positive():
    from eledger.redaction import redact_text
    assert redact_text("hello world") == "hello world"
    assert redact_text("count=5") == "count=5"
