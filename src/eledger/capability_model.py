"""Capability model for eLedger Self-Evolution Engine.

Maps required capabilities to status, evidence, and tests.
Statuses: PASS, PARTIAL, NOT_IMPLEMENTED, UNKNOWN.
"""

from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class Capability:
    id: str
    name: str
    status: str  # PASS | PARTIAL | NOT_IMPLEMENTED | UNKNOWN
    evidence: str
    tests: List[str]
    reuse: str
    gaps: str


CAPABILITIES: List[Capability] = [
    Capability("C1", "Read-only session ingestion", "PASS",
               "HermesStateDbReader (v23), RequestDumpReader",
               ["test_hermes_reader.py", "test_request_dump_reader.py"],
               "Existing eLedger readers",
               "Only v23 schema; no live DB inspection performed"),
    Capability("C2", "Evidence provenance preservation", "PASS",
               "NormalizedSession.provenance retained; test_provenance_preserved",
               ["test_pipeline.py"],
               "Existing ingestion", "Synthetic only"),
    Capability("C3", "Redaction", "PASS",
               "redaction.py covers report/manifest/CLI/request dumps",
               ["test_redaction.py"],
               "Existing redaction module", "Pattern set not exhaustive"),
    Capability("C4", "Publisher safety (path/timeout/divergence)", "PASS",
               "publisher.py allowlist, timeouts, divergence check, mocked tests",
               ["test_publisher.py"],
               "Existing publisher", "Symlink unverified on Windows"),
    Capability("C5", "Filesystem/symlink safety", "PARTIAL",
               "Traversal + absolute-path + symlink tests (symlink skipped on Windows)",
               ["test_publisher.py"],
               "Existing publisher path checks", "Symlink TOCTOU not tested"),
    Capability("C6", "Real source adapters", "NOT_IMPLEMENTED",
               "Only Hermes v23 + request dumps; no broad provider coverage",
               ["test_hermes_reader_hardening.py"],
               "Existing readers", "No live adapter verification"),
    Capability("C7", "Real GitHub publication", "NOT_IMPLEMENTED",
               "Dry-run + local disposable remote integration only",
               ["test_publisher.py"],
               "Existing publisher", "No real remote exercised"),
    Capability("C8", "Attribution accuracy", "PARTIAL",
               "5 synthetic labeled cases; conservative classifier",
               ["test_attribution_corpus.py"],
               "Existing attribution module", "No real-world accuracy"),
    Capability("C9", "Acceptance matrix reconciliation", "PASS",
               "21 PASS / 1 PARTIAL / 2 NOT IMPLEMENTED",
               ["docs/acceptance-matrix.md"],
               "Docs", "Counts based on reported evidence"),
    Capability("C10", "Capability model (machine-readable)", "PASS",
               "This module provides machine-readable capability list",
               ["test_capability_model.py"],
               "New (this milestone)", "Initial version"),
]


def get_capability(cap_id: str) -> Optional[Capability]:
    for c in CAPABILITIES:
        if c.id == cap_id:
            return c
    return None


def all_capabilities() -> List[dict]:
    return [asdict(c) for c in CAPABILITIES]


def status_counts() -> dict:
    counts = {"PASS": 0, "PARTIAL": 0, "NOT_IMPLEMENTED": 0, "UNKNOWN": 0}
    for c in CAPABILITIES:
        counts[c.status] = counts.get(c.status, 0) + 1
    return counts
