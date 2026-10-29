"""End-to-end synthetic pipeline tests."""
import json, tempfile, os
from eledger.pipeline import run_pipeline
from eledger.models import RunManifest

def test_e2e_synthetic(tmp_path):
    records = [
        {"meta": {"session_id": "s1", "source": "synthetic"}, "messages": [{"id": 1, "role": "user", "content": "let us do test driven development red green"}]},
        {"meta": {"session_id": "s2", "source": "synthetic"}, "messages": [{"id": 2, "role": "user", "content": "root cause hypothesis needed"}]},
        {"meta": {"session_id": "s3", "source": "synthetic"}, "messages": [{"id": 3, "role": "user", "content": "hello"}]},
    ]
    res = run_pipeline(records, "run-e2e", str(tmp_path))
    assert os.path.exists(res["report"])
    assert os.path.exists(res["manifest"])
    data = json.load(open(res["report"]))
    assert data["sessions_examined"] == 3
    assert data["sessions_excluded"] == 0
    # recurrence denominator reconciles
    for c in data["candidates"]:
        assert c["recurrence_denominator"] == 3
    # manifest validates
    m = RunManifest(**json.load(open(res["manifest"])))
    m.validate()
    assert m.status == "complete"

def test_e2e_malformed_record(tmp_path):
    records = [
        {"meta": {"session_id": "s1", "source": "synthetic"}, "messages": [{"id": 1, "role": "user", "content": "TDD red green"}]},
        "not a dict",
    ]
    res = run_pipeline(records, "run-mal", str(tmp_path))
    data = json.load(open(res["report"]))
    assert data["sessions_examined"] == 1
    assert data["sessions_excluded"] == 1
    assert len(data["retrieval_failures"]) == 1

def test_e2e_no_overwrite(tmp_path):
    records = [{"meta": {"session_id": "s1", "source": "synthetic"}, "messages": [{"id": 1, "role": "user", "content": "hi"}]}]
    run_pipeline(records, "run-x", str(tmp_path))
    import pytest
    with pytest.raises(FileExistsError):
        run_pipeline(records, "run-x", str(tmp_path))

def test_e2e_classifications(tmp_path):
    records = [{"meta": {"session_id": "s1", "source": "synthetic"}, "messages": [{"id": 1, "role": "user", "content": "TDD"}]}]
    res = run_pipeline(records, "run-cls", str(tmp_path))
    data = json.load(open(res["report"]))
    for c in data["candidates"]:
        assert c["classification"] in ("confirmed", "inferred", "unknown")
        assert c["classification"] != "confirmed"  # no explicit invocation in synthetic
        assert c["disposition"] == "insufficient_evidence"


def test_e2e_redaction_survives_publisher(tmp_path):
    import os, subprocess, tempfile
    def _git(cmd, cwd):
        return subprocess.run(["git"] + cmd, cwd=cwd, capture_output=True, text=True)
    work = str(tmp_path / "work"); remote = str(tmp_path / "remote.git")
    os.makedirs(work)
    _git(["init", "-b", "main"], work)
    _git(["config", "user.email", "t@t.com"], work)
    _git(["config", "user.name", "t"], work)
    _git(["init", "--bare", remote], str(tmp_path))
    _git(["remote", "add", "origin", remote], work)
    (tmp_path / "work" / "README.md").write_text("hi")
    _git(["add", "README.md"], work)
    _git(["commit", "-m", "init"], work)
    _git(["push", "-u", "origin", "main"], work)
    from eledger.publisher import Publisher
    secret = "sk-supersecrettoken1234567890"
    records = [{"meta": {"session_id": "s1", "source": "synthetic"}, "messages": [{"id": 1, "role": "user", "content": f"token={secret}"}]}]
    res = run_pipeline(records, "run-red", work)
    pub = Publisher(work, allowed_files={"run-red.json", "run-red-manifest.json"}, dry_run=True)
    r = pub.publish(res["manifest"], [res["report"]], "msg")
    assert r["status"] == "dry_run_ok"
    report_text = open(res["report"]).read()
    manifest_text = open(res["manifest"]).read()
    assert secret not in report_text
    assert secret not in manifest_text


def test_provenance_preserved(tmp_path):
    records = [{"meta": {"session_id": "s1", "source": "synthetic"}, "messages": [{"id": 1, "role": "user", "content": "hi"}], "provenance": {"k": "v"}}]
    ns = normalize_session(records[0]) if False else None
    from eledger.ingestion import normalize_session
    ns = normalize_session(records[0])
    assert ns.provenance == {"k": "v"}
