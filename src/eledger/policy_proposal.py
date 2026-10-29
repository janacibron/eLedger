"""Generate evidence-backed policy proposals from observed patterns."""

from dataclasses import dataclass, asdict
from typing import List


@dataclass
class PolicyProposal:
    pattern: str
    evidence: List[str]
    confidence: str
    root_cause: str
    proposed_change: str
    expected_benefit: str
    side_effects: str
    regression_tests: List[str]
    rollback: str
    evaluation_criteria: str

    def to_dict(self):
        return asdict(self)


def propose_from_pattern(pattern: str, evidence: List[str], confidence: str = "low") -> PolicyProposal:
    return PolicyProposal(
        pattern=pattern,
        evidence=evidence,
        confidence=confidence,
        root_cause="Observed recurring pattern in engineering evidence.",
        proposed_change="Add a regression test and fail-closed guard for the observed pattern.",
        expected_benefit="Reduce recurrence and improve detection.",
        side_effects="May increase test runtime; requires review.",
        regression_tests=["Add synthetic test reproducing the pattern."],
        rollback="Revert the guard if false positives exceed threshold.",
        evaluation_criteria="Measure recurrence reduction over N runs.",
    )
