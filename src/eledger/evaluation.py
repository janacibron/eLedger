"""Evaluation and decision gates."""
from .models import EvaluationResult


def evaluate_candidate(candidate, evidence_list):
    criteria_passed = []
    criteria_failed = []
    criteria_unknown = []
    # evidence sufficiency
    if candidate.recurrence_denominator > 0 and candidate.recurrence_count >= 2:
        criteria_passed.append("recurrence_threshold")
    else:
        criteria_unknown.append("recurrence_threshold")
    if candidate.classification == "confirmed":
        criteria_passed.append("confirmed_invocation")
    else:
        criteria_unknown.append("confirmed_invocation")
    if len(candidate.evidence_ids) > 0:
        criteria_passed.append("has_evidence_refs")
    else:
        criteria_failed.append("has_evidence_refs")
    # disposition
    if "confirmed_invocation" in criteria_passed and "recurrence_threshold" in criteria_passed:
        disp = "accepted_for_review"
    else:
        disp = "insufficient_evidence"
    res = EvaluationResult(
        candidate_id=candidate.candidate_id,
        criteria_passed=criteria_passed,
        criteria_failed=criteria_failed,
        criteria_unknown=criteria_unknown,
        disposition=disp,
    )
    return res
