"""Candidate artifact model for eLedger sandbox lifecycle."""

import hashlib
import json
import uuid
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Candidate:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: str = "0.1.0"
    provenance: str = "synthetic"
    purpose: str = ""
    dependencies: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    artifact_path: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return Candidate(**d)

    def content_hash(self) -> Optional[str]:
        if self.artifact_path and Path(self.artifact_path).exists():
            return hashlib.sha256(Path(self.artifact_path).read_bytes()).hexdigest()
        return None
PYEOF