"""Sandboxed execution and controlled promotion for eLedger.

Provides a minimal isolated workspace for candidate artifacts and a
promotion gate that requires passing validation before copying to target.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List


class Sandbox:
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(tempfile.mkdtemp(prefix="eledger-sandbox-"))
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self.base_dir

    def run(self, cmd: List[str], timeout: int = 60, env: Dict[str, str] = None) -> Dict[str, Any]:
        e = dict(os.environ)
        # least privilege: strip common secret-bearing vars
        for k in ("GITHUB_TOKEN", "AWS_SECRET_ACCESS_KEY", "OPENAI_API_KEY"):
            e.pop(k, None)
        if env:
            e.update(env)
        try:
            r = subprocess.run(cmd, cwd=str(self.base_dir), capture_output=True, text=True, timeout=timeout, env=e)
            return {"returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr, "timed_out": False}
        except subprocess.TimeoutExpired:
            return {"returncode": -1, "stdout": "", "stderr": "timed out", "timed_out": True}

    def cleanup(self):
        shutil.rmtree(self.base_dir, ignore_errors=True)


import hashlib
import json


def _hash(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def promote(candidate_path, target_path, validated, expected_hash=None, backup=True):
    """Promote candidate to target only if validated and integrity matches.

    Returns dict with status and details. No-overwrite by default unless backup.
    """
    cp = Path(candidate_path)
    tp = Path(target_path)
    if not validated:
        return {"status": "rejected", "reason": "not validated"}
    if not cp.exists():
        return {"status": "rejected", "reason": "candidate missing"}
    cand_hash = _hash(cp)
    if expected_hash is not None and cand_hash != expected_hash:
        return {"status": "rejected", "reason": "hash mismatch (TOCTOU)"}
    # TOCTOU re-check: re-hash right before copy
    if _hash(cp) != cand_hash:
        return {"status": "rejected", "reason": "hash changed during promotion"}
    tp.parent.mkdir(parents=True, exist_ok=True)
    backup_path = None
    if tp.exists():
        if not backup:
            return {"status": "rejected", "reason": "target exists (no-overwrite)"}
        backup_path = tp.with_suffix(tp.suffix + ".bak")
        if backup_path.exists():
            return {"status": "rejected", "reason": "backup exists"}
        tp.rename(backup_path)
    try:
        shutil.copy2(cp, tp)
        if _hash(tp) != cand_hash:
            # rollback
            tp.unlink(missing_ok=True)
            if backup_path and backup_path.exists():
                backup_path.rename(tp)
            return {"status": "failed", "reason": "post-copy hash mismatch"}
    except Exception as e:
        if backup_path and backup_path.exists():
            backup_path.rename(tp)
        return {"status": "failed", "reason": str(e)}
    return {"status": "promoted", "hash": cand_hash, "backup": str(backup_path) if backup_path else None}


def rollback(target_path):
    tp = Path(target_path)
    backup = tp.with_suffix(tp.suffix + ".bak")
    if not backup.exists():
        return {"status": "no_backup"}
    tp.unlink(missing_ok=True)
    backup.rename(tp)
    return {"status": "rolled_back"}
