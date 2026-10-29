"""Adversarial publisher tests."""
import os, subprocess, json, pathlib, tempfile
import pytest
from eledger.publisher import Publisher, _contains_secret
from eledger.audit import write_manifest
from eledger.models import RunManifest


def _git(cmd, cwd):
    return subprocess.run(["git"] + cmd, cwd=cwd, capture_output=True, text=True)


def make_repo(tmp):
    work = os.path.join(tmp, "work")
    remote = os.path.join(tmp, "remote.git")
    os.makedirs(work)
    _git(["init", "-b", "main"], work)
    _git(["config", "user.email", "t@t.com"], work)
    _git(["config", "user.name", "t"], work)
    _git(["init", "--bare", remote], tmp)
    _git(["remote", "add", "origin", remote], work)
    pathlib.Path(work, "README.md").write_text("hi")
    _git(["add", "README.md"], work)
    _git(["commit", "-m", "init"], work)
    _git(["push", "-u", "origin", "main"], work)
    return work, remote


def test_secret_bypass_base64_still_scanned(tmp_path):
    # secret split across lines still contains pattern
    assert _contains_secret("token = abc123xyz") is True

import sys
@pytest.mark.skipif(sys.platform == "win32", reason="symlink privilege")
def test_symlink_rejected(tmp_path):
    work, remote = make_repo(str(tmp_path))
    real = os.path.join(work, "real.json")
    pathlib.Path(real).write_text("{}")
    link = os.path.join(work, "link.json")
    os.symlink(real, link)
    manifest_path = os.path.join(work, "m.json")
    m = RunManifest(run_id="r", started_at="2026-01-01T00:00:00Z", status="complete")
    write_manifest(m, pathlib.Path(manifest_path))
    pub = Publisher(work, allowed_files={"m.json", "link.json"}, dry_run=True)
    ok, errs = pub.validate_artifacts(manifest_path, [link])
    assert ok is False

def test_tampered_artifact_rejected(tmp_path):
    work, remote = make_repo(str(tmp_path))
    artifact = os.path.join(work, "report.json")
    pathlib.Path(artifact).write_text('{"x":1}')
    manifest_path = os.path.join(work, "m.json")
    m = RunManifest(run_id="r", started_at="2026-01-01T00:00:00Z", status="complete")
    m.artifact_hashes["report.json"] = "deadbeef"
    write_manifest(m, pathlib.Path(manifest_path))
    pub = Publisher(work, allowed_files={"m.json", "report.json"}, dry_run=True)
    ok, errs = pub.validate_artifacts(manifest_path, [artifact])
    assert ok is False
    assert any("hash mismatch" in e for e in errs)

def test_not_allowlisted_rejected(tmp_path):
    work, remote = make_repo(str(tmp_path))
    artifact = os.path.join(work, "secret.txt")
    pathlib.Path(artifact).write_text("x")
    manifest_path = os.path.join(work, "m.json")
    m = RunManifest(run_id="r", started_at="2026-01-01T00:00:00Z", status="complete")
    write_manifest(m, pathlib.Path(manifest_path))
    pub = Publisher(work, allowed_files={"m.json"}, dry_run=True)
    res = pub.publish(manifest_path, [artifact], "msg")
    assert res["status"] == "rejected"
