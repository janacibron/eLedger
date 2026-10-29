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
