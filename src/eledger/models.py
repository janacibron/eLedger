"""Core domain models and contracts for eLedger."""
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import hashlib, json


class ValidationError(Exception):
    pass


def _require(cond, msg):
    if not cond:
        raise ValidationError(msg)


@dataclass
class SessionMeta:
    session_id: str
    source: str
    started_at: Optional[float] = None
    ended_at: Optional[float] = None
    message_count: int = 0
    schema_version: int = 1

    def validate(self):
        _require(bool(self.session_id), "session_id required")
        _require(bool(self.source), "source required")
        if self.started_at is not None and self.ended_at is not None:
            _require(self.ended_at >= self.started_at, "ended_at < started_at")
        _require(self.message_count >= 0, "message_count >= 0")


@dataclass
class MessageRecord:
    message_id: Any
    session_id: str
    role: str
    content: str
    timestamp: Optional[float] = None
    schema_version: int = 1

    def validate(self):
        _require(self.session_id, "session_id required")
        _require(self.role in ("user", "assistant", "system", "tool"), f"invalid role {self.role}")
        _require(self.content is not None, "content required")


@dataclass
class NormalizedSession:
    meta: SessionMeta
    messages: List[MessageRecord] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)
    retrieval_failures: List[str] = field(default_factory=list)

    def validate(self):
        self.meta.validate()
        for m in self.messages:
            m.validate()
            _require(m.session_id == self.meta.session_id, "message session_id mismatch")
        # stable ordering by message_id then timestamp
        ids = [m.message_id for m in self.messages]
        # allow duplicates only if explicitly tracked; here require unique
        if len(set(str(i) for i in ids)) != len(ids):
            raise ValidationError("duplicate message_id within session")


@dataclass
class Evidence:
    evidence_id: str
    evidence_type: str
    session_id: str
    message_ids: List[Any] = field(default_factory=list)
    classification: str = "unknown"  # confirmed/inferred/unknown
    grade: str = "C"  # A/B/C
    observation: str = ""
    interpretation: str = ""
    quote_redacted: str = ""
    recurrence_count: int = 0
    recurrence_denominator: int = 0
    counter_evidence: List[str] = field(default_factory=list)
    skill_invocation: str = "unknown"
    action_outcome: str = "unknown"
    schema_version: int = 1

    def validate(self):
        _require(self.evidence_id, "evidence_id required")
        _require(self.classification in ("confirmed", "inferred", "unknown"), "bad classification")
        _require(self.grade in ("A", "B", "C"), "bad grade")
        _require(self.recurrence_denominator >= 0, "denom >=0")
        if self.recurrence_denominator > 0:
            assert 0 <= self.recurrence_count <= self.recurrence_denominator

    def to_dict(self):
        return asdict(self)


@dataclass
class Candidate:
    candidate_id: str
    title: str
    skill_id: str
    skill_version: str
    rationale: str = ""
    evidence_ids: List[str] = field(default_factory=list)
    counter_evidence: List[str] = field(default_factory=list)
    recurrence_count: int = 0
    recurrence_denominator: int = 0
    classification: str = "inferred"
    grade: str = "C"
    acceptance_criteria: List[str] = field(default_factory=list)
    disposition: str = "insufficient_evidence"
    recommendation: str = "INSUFFICIENT_EVIDENCE"
    schema_version: int = 1

    def validate(self):
        _require(self.candidate_id, "candidate_id required")
        _require(self.skill_id, "skill_id required")
        _require(self.classification in ("confirmed", "inferred", "unknown"), "bad classification")
        _require(self.disposition in ("proposed", "insufficient_evidence", "rejected", "accepted_for_review", "approved"), "bad disposition")
        _require(self.recommendation in ("PROPOSE", "INSUFFICIENT_EVIDENCE", "NO_CHANGE_JUSTIFIED", "REJECT"), "bad recommendation")
        if self.recurrence_denominator > 0:
            assert 0 <= self.recurrence_count <= self.recurrence_denominator

    def to_dict(self):
        return asdict(self)


@dataclass
class EvaluationResult:
    candidate_id: str
    criteria_passed: List[str] = field(default_factory=list)
    criteria_failed: List[str] = field(default_factory=list)
    criteria_unknown: List[str] = field(default_factory=list)
    disposition: str = "insufficient_evidence"
    schema_version: int = 1

    def to_dict(self):
        return asdict(self)


@dataclass
class RunManifest:
    run_id: str
    started_at: str
    completed_at: Optional[str] = None
    eledger_version: str = "0.1.0"
    window_start: Optional[str] = None
    window_end: Optional[str] = None
    source_scope: str = ""
    sessions_in_window: int = 0
    sessions_examined: int = 0
    sessions_excluded: int = 0
    retrieval_failures: List[str] = field(default_factory=list)
    candidate_count: int = 0
    artifact_hashes: Dict[str, str] = field(default_factory=dict)
    status: str = "incomplete"  # incomplete | complete
    limitations: List[str] = field(default_factory=list)
    schema_version: int = 1

    def validate(self):
        _require(self.run_id, "run_id required")
        _require(self.status in ("incomplete", "complete"), "bad status")

    def to_dict(self):
        return asdict(self)

    def artifact_hash(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()


@dataclass
class ApprovalRecord:
    candidate_id: str
    reviewer: str
    decision: str  # approved/rejected
    rationale: str = ""
    timestamp: str = ""
    scope: str = ""
    schema_version: int = 1

    def validate(self):
        _require(self.candidate_id, "candidate_id required")
        _require(self.reviewer, "reviewer required")
        _require(self.decision in ("approved", "rejected"), "bad decision")
