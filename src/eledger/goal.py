"""Goal model and goal-aware matching for eLedger."""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any


@dataclass
class Goal:
    original: str
    objective: str = ""
    functional: List[str] = field(default_factory=list)
    non_functional: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


def goal_keywords(goal: Goal) -> set:
    words = set()
    for text in [goal.original, goal.objective] + goal.functional + goal.success_criteria:
        for w in text.lower().split():
            words.add(w.strip(".,;:!?"))
    return words


def goal_match_score(goal: Goal, program: Dict[str, Any]) -> float:
    """Score how well a program matches a goal (0-100)."""
    kw = goal_keywords(goal)
    if not kw:
        return 0.0
    text = " ".join([
        program.get("path", ""),
        " ".join(program.get("manifests", [])),
        " ".join(program.get("files", [])),
    ]).lower()
    hits = sum(1 for w in kw if w in text)
    return round(100.0 * hits / len(kw), 2)


def rank_for_goal(goal: Goal, programs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ranked = []
    for p in programs:
        ranked.append({**p, "goal_score": goal_match_score(goal, p)})
    ranked.sort(key=lambda x: (-x["goal_score"], x.get("path", "")))
    return ranked
