"""Audit ledger and manifests."""
import json, hashlib
from pathlib import Path
from .redaction import redact
from .models import RunManifest


def write_manifest(manifest: RunManifest, path: Path):
    manifest.validate()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    path.write_text(json.dumps(redact(manifest.to_dict()), indent=2), encoding="utf-8")
    return path


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
