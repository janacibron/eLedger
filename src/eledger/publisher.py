"""Secure GitHub audit publisher (disabled by default)."""
import hashlib, os, subprocess, json
from pathlib import Path
from .models import RunManifest

PROHIBITED_EXTENSIONS = {".db", ".sqlite", ".sqlite3", ".db-wal", ".db-shm", ".log"}
PROHIBITED_NAMES = {"state.db", "transcripts"}


def _run(cmd, cwd=None, timeout=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def _hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _contains_secret(text):
    import re
    patterns = [r"sk-[A-Za-z0-9]{10,}", r"token\s*=\s*\S+", r"password\s*=\s*\S+", r"ghp_[A-Za-z0-9]{20,}", r"gho_[A-Za-z0-9]{20,}"]
    for p in patterns:
        if re.search(p, text, re.I):
            return True
    return False


class Publisher:
    def __init__(self, repo_path, allowed_files=None, dry_run=True):
        self.repo_path = Path(repo_path)
        self.allowed_files = set(allowed_files or [])
        self.dry_run = dry_run

    def validate_artifacts(self, manifest_path, artifact_paths):
        """Validate manifest complete and hashes match. Returns (ok, errors)."""
        errors = []
        mp = Path(manifest_path)
        if not mp.exists():
            errors.append("manifest missing")
            return False, errors
        try:
            data = json.loads(mp.read_text())
            m = RunManifest(**data)
            m.validate()
        except Exception as e:
            errors.append(f"manifest invalid: {e}")
            return False, errors
        if m.status != "complete":
            errors.append("manifest not complete")
        for ap in artifact_paths:
            p = Path(ap)
            if not p.exists():
                errors.append(f"artifact missing: {ap}")
                continue
            if p.suffix in PROHIBITED_EXTENSIONS or p.name in PROHIBITED_NAMES:
                errors.append(f"prohibited artifact: {ap}")
            # hash check if in manifest
            if p.name in m.artifact_hashes:
                if m.artifact_hashes[p.name] != _hash_file(p):
                    errors.append(f"hash mismatch: {p.name}")
            # secret scan
            try:
                if _contains_secret(p.read_text(errors="ignore")):
                    errors.append(f"secret detected in {ap}")
            except Exception:
                pass
        # path traversal / symlink check
        for ap in artifact_paths + [str(manifest_path)]:
            p = Path(ap).resolve()
            try:
                p.relative_to(self.repo_path.resolve())
            except ValueError:
                errors.append(f"path escapes repo: {ap}")
            if p.is_symlink():
                errors.append(f"symlink not allowed: {ap}")
        return len(errors) == 0, errors

    def stage(self, files):
        """Stage only allowlisted files. Returns (ok, errors)."""
        errors = []
        for f in files:
            name = Path(f).name
            if name not in self.allowed_files:
                errors.append(f"not allowlisted: {f}")
                continue
            p = self.repo_path / f
            if not p.exists():
                errors.append(f"missing: {f}")
                continue
            # path safety
            try:
                p.resolve().relative_to(self.repo_path.resolve())
            except ValueError:
                errors.append(f"path escapes: {f}")
                continue
            if p.is_symlink():
                errors.append(f"symlink: {f}")
                continue
        if errors:
            return False, errors
        if self.dry_run:
            return True, []
        # actual git add for each
        for f in files:
            try:
                r = _run(["git", "add", "--", f], cwd=str(self.repo_path), timeout=10)
            except subprocess.TimeoutExpired:
                return False, [f"git add timed out for {f}: outcome unknown"]
            if r.returncode != 0:
                errors.append(f"git add failed: {f}: {r.stderr}")
        return len(errors) == 0, errors

    def check_divergence(self):
        """Fetch and check if local is behind remote. Returns (diverged, msg)."""
        try:
            r = _run(["git", "fetch", "origin"], cwd=str(self.repo_path), timeout=10)
        except subprocess.TimeoutExpired:
            return True, "fetch timed out"
        if r.returncode != 0:
            return True, f"fetch failed: {r.stderr}"
        try:
            r = _run(["git", "rev-list", "--count", "HEAD..@{u}"], cwd=str(self.repo_path), timeout=10)
        except subprocess.TimeoutExpired:
            return True, "rev-list timed out"
        if r.returncode != 0:
            return False, "no upstream or detached"
        behind = int(r.stdout.strip() or "0")
        if behind > 0:
            return True, f"behind remote by {behind} commits"
        return False, "up to date"

    def publish(self, manifest_path, artifact_paths, commit_message, branch="main"):
        """Publish validated artifacts. Returns dict with status."""
        ok, errors = self.validate_artifacts(manifest_path, artifact_paths)
        if not ok:
            return {"status": "rejected", "errors": errors}
        # check all files allowlisted
        all_files = [Path(manifest_path).name] + [Path(p).name for p in artifact_paths]
        for f in all_files:
            if f not in self.allowed_files:
                return {"status": "rejected", "errors": [f"not allowlisted: {f}"]}
        # divergence check
        div, msg = self.check_divergence()
        if div:
            return {"status": "rejected", "errors": [f"divergence: {msg}"]}
        # stage
        ok, errors = self.stage([str(Path(manifest_path).relative_to(self.repo_path))] + [str(Path(p).relative_to(self.repo_path)) for p in artifact_paths])
        if not ok:
            return {"status": "rejected", "errors": errors}
        if self.dry_run:
            return {"status": "dry_run_ok", "errors": []}
        # commit
        try:
            r = _run(["git", "commit", "-m", commit_message], cwd=str(self.repo_path), timeout=30)
        except subprocess.TimeoutExpired:
            return {"status": "commit_timeout", "errors": ["commit timed out; outcome unknown — verify repository state before retrying"]}
        if r.returncode != 0:
            return {"status": "commit_failed", "errors": [r.stderr]}
        # push (no force)
        try:
            r = _run(["git", "push", "origin", branch], cwd=str(self.repo_path), timeout=30)
        except subprocess.TimeoutExpired:
            return {"status": "push_timeout", "errors": ["push timed out; outcome unknown — verify remote state before retrying"]}
        if r.returncode != 0:
            return {"status": "push_failed", "errors": [r.stderr]}
        return {"status": "published", "errors": []}
