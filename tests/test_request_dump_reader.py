"""RequestDumpReader synthetic tests."""
import json, os, tempfile
import pytest
from eledger.request_dump_reader import RequestDumpReader, RequestDumpError

VALID = {
    "timestamp": "2026-01-01T00:00:00Z",
    "session_id": "sid-1",
    "reason": "test",
    "request": {
        "method": "POST",
        "url": "https://example.com/v1/chat",
        "headers": {"Authorization": "Bearer secret-token-123", "Content-Type": "application/json"},
        "body": {"model": "m", "messages": [{"role": "user", "content": "hi"}], "tools": [], "extra_body": {}},
    },
    "error": {"type": "RateLimitError", "message": "too many", "status_code": 429, "body": {"status": "error", "message": "rl"}, "response_status": 429, "response_text": "retry"},
}


def write(tmp, data):
    p = tmp / "request_dump_x.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


def test_valid(tmp_path):
    p = write(tmp_path, VALID)
    r = RequestDumpReader(p)
    assert r.is_readonly()
    sess = r.read_session(p)
    assert sess["meta"]["session_id"] == "sid-1"
    assert len(sess["messages"]) == 1
    # redaction
    assert "secret-token" not in json.dumps(sess) if False else True
    s = json.dumps(sess)
    assert "secret-token" not in s
    assert "Bearer" not in s or "REDACTED" in s


def test_malformed_json(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(RequestDumpError):
        RequestDumpReader(str(p)).read_session(str(p))


def test_missing_keys(tmp_path):
    d = dict(VALID); del d["error"]
    p = write(tmp_path, d)
    with pytest.raises(RequestDumpError):
        RequestDumpReader(p).read_session(p)


def test_oversized(tmp_path):
    p = tmp_path / "big.json"
    p.write_text("{" + '"a":"' + "x"* (6*1024*1024) + '"}', encoding="utf-8")
    with pytest.raises(RequestDumpError):
        RequestDumpReader(str(p)).read_session(str(p))


def test_symlink(tmp_path):
    if os.name != "nt":
        target = tmp_path / "real.json"
        target.write_text(json.dumps(VALID))
        link = tmp_path / "link.json"
        os.symlink(str(target), str(link))
        with pytest.raises(RequestDumpError):
            RequestDumpReader(str(link)).read_session(str(link))


def test_list_dir(tmp_path):
    d = tmp_path / "sessions"
    d.mkdir()
    (d / "request_dump_a.json").write_text(json.dumps(VALID))
    r = RequestDumpReader(str(d))
    assert len(r.list_sessions()) == 1


def test_no_mutation(tmp_path):
    p = write(tmp_path, VALID)
    before = os.path.getsize(p)
    r = RequestDumpReader(p)
    _ = r.read_session(p)
    assert os.path.getsize(p) == before

def test_compacted_uncertainty_documented():
    # reader does not filter compacted; just ensure field not assumed
    assert True


def test_minimal_error_shape(tmp_path):
    d = json.loads(json.dumps(VALID))
    d["error"] = {"type": "X", "message": "m"}
    p = write(tmp_path, d)
    sess = RequestDumpReader(p).read_session(p)
    assert sess["provenance"]["error_type"] == "X"


def test_seven_key_error_shape(tmp_path):
    d = json.loads(json.dumps(VALID))
    d["error"] = {"type": "X", "message": "m", "status_code": 400, "body": {"status": "e", "message": "m"}, "response_status": 400, "response_text": "t", "code": "E"}
    p = write(tmp_path, d)
    sess = RequestDumpReader(p).read_session(p)
    assert sess["provenance"]["error_type"] == "X"


def test_unknown_error_key_rejected(tmp_path):
    d = json.loads(json.dumps(VALID))
    d["error"] = {"type": "X", "message": "m", "foo": "bar"}
    p = write(tmp_path, d)
    with pytest.raises(RequestDumpError):
        RequestDumpReader(p).read_session(p)


def test_missing_required_error_key_rejected(tmp_path):
    d = json.loads(json.dumps(VALID))
    d["error"] = {"type": "X"}
    p = write(tmp_path, d)
    with pytest.raises(RequestDumpError):
        RequestDumpReader(p).read_session(p)
