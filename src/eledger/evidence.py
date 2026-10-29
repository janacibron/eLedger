"""Evidence extraction and candidate construction."""
from .models import Evidence, Candidate


def classify_evidence(explicit_invocation: bool, consistent_behavior: bool, sufficient_context: bool) -> str:
    if explicit_invocation and sufficient_context:
        return "confirmed"
    if consistent_behavior and sufficient_context:
        return "inferred"
    return "unknown"


def build_evidence(eid, session_id, message_ids, classification, grade, observation, interpretation="", quote="", skill_invocation="unknown", action_outcome="unknown"):
    e = Evidence(
        evidence_id=eid, evidence_type="session_signal", session_id=session_id,
        message_ids=list(message_ids), classification=classification, grade=grade,
        observation=observation, interpretation=interpretation, quote_redacted=quote,
        skill_invocation=skill_invocation, action_outcome=action_outcome,
    )
    e.validate()
    return e


def build_candidate(cid, title, skill_id, skill_version, evidence_ids, recurrence_count, recurrence_denominator, classification="inferred", grade="C"):
    c = Candidate(
        candidate_id=cid, title=title, skill_id=skill_id, skill_version=skill_version,
        evidence_ids=list(evidence_ids), recurrence_count=recurrence_count,
        recurrence_denominator=recurrence_denominator, classification=classification, grade=grade,
        disposition="insufficient_evidence", recommendation="INSUFFICIENT_EVIDENCE",
    )
    c.validate()
    return c
