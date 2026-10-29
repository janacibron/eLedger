"""Baseline + model tests."""
import json, tempfile, os
import pytest
from eledger.models import SessionMeta, MessageRecord, NormalizedSession, Evidence, Candidate, RunManifest, ValidationError
from eledger.ingestion import normalize_session
from eledger.evidence import classify_evidence, build_evidence, build_candidate
from eledger.evaluation import evaluate_candidate
from eledger.audit import write_manifest, hash_file

def test_package_version():
    import eledger
    assert eledger.__version__ == "0.1.0"

def test_session_validation():
    m = SessionMeta(session_id="s1", source="test", started_at=10.0, ended_at=5.0)
    try:
        m.validate(); assert False
    except ValidationError:
        pass

def test_message_role_validation():
    m = MessageRecord(message_id=1, session_id="s1", role="bogus", content="x")
    try:
        m.validate(); assert False
    except ValidationError:
        pass

def test_normalize_session():
    ns = normalize_session({"meta":{"session_id":"s1","source":"t"},"messages":[{"id":1,"role":"user","content":"hi"}]})
    assert ns.meta.session_id == "s1"
    assert len(ns.messages) == 1

def test_normalize_rejects_bad():
    try:
        normalize_session("not a dict"); assert False
    except ValidationError:
        pass

def test_evidence_classification():
    assert classify_evidence(True, True, True) == "confirmed"
    assert classify_evidence(False, True, True) == "inferred"
    assert classify_evidence(False, False, False) == "unknown"

def test_evidence_validation():
    e = build_evidence("e1","s1",[1],"inferred","C","obs")
    e.validate()

def test_candidate_default_insufficient():
    c = build_candidate("c1","t","skill","1.0",["e1"],1,5)
    assert c.disposition == "insufficient_evidence"
    assert c.recommendation == "INSUFFICIENT_EVIDENCE"

def test_evaluation_insufficient():
    c = build_candidate("c1","t","skill","1.0",["e1"],1,5)
    r = evaluate_candidate(c, [])
    assert r.disposition == "insufficient_evidence"

def test_run_manifest_no_overwrite(tmp_path):
    m = RunManifest(run_id="r1", started_at="2026-01-01T00:00:00Z")
    p = tmp_path / "m.json"
    write_manifest(m, p)
    with pytest.raises(FileExistsError):
        write_manifest(m, p)

def test_topic_similarity_not_invocation():
    # inferred classification never upgrades to confirmed without explicit invocation
    assert classify_evidence(False, True, True) != "confirmed"
