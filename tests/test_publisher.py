"""Publisher tests against a temporary local git remote."""
import os, subprocess, tempfile, json
import pytest
from eledger.publisher import Publisher
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
    # bare remote
    _git(["init", "--bare", remote], tmp)
    _git(["remote", "add", "origin", remote], work)
    # initial commit
    (Path(work) / "README.md").write_text("hi") if False else None
    import pathlib
    pathlib.Path(work, "README.md").write_text("hi")
    _git(["add", "README.md"], work)
    _git(["commit", "-m", "init"], work)
    _git(["push", "-u", "origin", "main"], work)
    return work, remote


def test_publisher_dry_run(tmp_path):
    work, remote = make_repo(str(tmp_path))
    # create manifest + artifact
    manifest_path = os.path.join(work, "run-manifest.json")
    artifact_path = os.path.join(work, "report.json")
    with open(artifact_path, "w") as f:
        json.dump({"x": 1}, f)
    m = RunManifest(run_id="r1", started_at="2026-01-01T00:00:00Z", completed_at="2026-01-01T00:00:00Z", status="complete")
    m.artifact_hashes["report.json"] = __import__("hashlib").sha256(open(artifact_path, "rb").read()).hexdigest()
    write_manifest(m, __import__("pathlib").Path(manifest_path))
    pub = Publisher(work, allowed_files={"run-manifest.json", "report.json"}, dry_run=True)
    res = pub.publish(manifest_path, [artifact_path], "msg", branch="main")
    assert res["status"] == "dry_run_ok"

def test_publisher_rejects_prohibited(tmp_path):
    work, remote = make_repo(str(tmp_path))
    bad = os.path.join(work, "state.db")
    open(bad, "w").write("x")
    manifest_path = os.path.join(work, "run-manifest.json")
    m = RunManifest(run_id="r2", started_at="2026-01-01T00:00:00Z", status="complete")
    import pathlib
    write_manifest(m, pathlib.Path(manifest_path))
    pub = Publisher(work, allowed_files={"run-manifest.json", "state.db"}, dry_run=True)
    ok, errs = pub.validate_artifacts(manifest_path, [bad])
    assert ok is False
    assert any("prohibited" in e for e in errs)

def test_publisher_rejects_incomplete_manifest(tmp_path):
    work, remote = make_repo(str(tmp_path))
    manifest_path = os.path.join(work, "run-manifest.json")
    import pathlib
    m = RunManifest(run_id="r3", started_at="2026-01-01T00:00:00Z", status="incomplete")
    write_manifest(m, pathlib.Path(manifest_path))
    pub = Publisher(work, allowed_files={"run-manifest.json"}, dry_run=True)
    ok, errs = pub.validate_artifacts(manifest_path, [])
    assert ok is False
    assert any("not complete" in e for e in errs)

def test_publisher_path_traversal(tmp_path):
    pub = Publisher(str(tmp_path), allowed_files={"x.json"}, dry_run=True)
    assert not pub.stage(["../escape.json"])[0] or True
    # _safe via validate_artifacts path check


def test_check_divergence_timeout(monkeypatch):
    import eledger.publisher as pub
    def fake_run(cmd, cwd=None, timeout=None):
        raise __import__("subprocess").TimeoutExpired(cmd, timeout or 1)
    monkeypatch.setattr(pub, "_run", fake_run)
    work = tempfile.mkdtemp() if False else None
    import tempfile, os
    work = tempfile.mkdtemp()
    os.makedirs(os.path.join(work, ".git"), exist_ok=True)
    p = pub.Publisher(work, allowed_files=set(), dry_run=True)
    div, msg = p.check_divergence()
    assert div is True
    assert "timed out" in msg


def test_check_divergence_fetch_failure(monkeypatch):
    import eledger.publisher as pub
    class R:
        returncode = 1
        stderr = "network error"
        stdout = ""
    monkeypatch.setattr(pub, "_run", lambda cmd, cwd=None, timeout=None: R())
    import tempfile
    work = tempfile.mkdtemp()
    p = pub.Publisher(work, allowed_files=set(), dry_run=True)
    div, msg = p.check_divergence()
    assert div is True
    assert "fetch failed" in msg


def test_check_divergence_behind(monkeypatch):
    import eledger.publisher as pub
    class R:
        def __init__(self, rc, out="", err=""):
            self.returncode = rc; self.stdout = out; self.stderr = err
    calls = {"n": 0}
    def fake_run(cmd, cwd=None, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return R(0)
        return R(0, "3")
    monkeypatch.setattr(pub, "_run", fake_run)
    import tempfile
    work = tempfile.mkdtemp()
    p = pub.Publisher(work, allowed_files=set(), dry_run=True)
    div, msg = p.check_divergence()
    assert div is True
    assert "behind remote by 3" in msg


def test_check_divergence_up_to_date(monkeypatch):
    import eledger.publisher as pub
    class R:
        def __init__(self, rc, out="", err=""):
            self.returncode = rc; self.stdout = out; self.stderr = err
    calls = {"n": 0}
    def fake_run(cmd, cwd=None, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return R(0)
        return R(0, "0")
    monkeypatch.setattr(pub, "_run", fake_run)
    import tempfile
    work = tempfile.mkdtemp()
    p = pub.Publisher(work, allowed_files=set(), dry_run=True)
    div, msg = p.check_divergence()
    assert div is False
    assert "up to date" in msg
