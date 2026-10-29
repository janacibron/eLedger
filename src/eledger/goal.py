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


def rank_for_goal(goal, programs):
    ranked = []
    for p in programs:
        ranked.append({**p, "goal_score": goal_match_score(goal, p)})
    ranked.sort(key=lambda x: (-x["goal_score"], x.get("path", "")))
    return ranked


def recommend_strategy(goal, programs):
    """Recommend a strategy based on goal match scores."""
    ranked = rank_for_goal(goal, programs)
    if not ranked:
        return {"strategy": "build_new", "reason": "no candidates found", "ranked": []}
    best = ranked[0]
    if best["goal_score"] >= 50:
        return {"strategy": "extend_existing", "candidate": best["path"], "reason": "best goal match", "ranked": ranked}
    if best["goal_score"] > 0:
        return {"strategy": "integrate_components", "candidate": best["path"], "reason": "partial match", "ranked": ranked}
    return {"strategy": "build_new", "reason": "no suitable candidate", "ranked": ranked}


def goal_report(goal, programs):
    rec = recommend_strategy(goal, programs)
    lines = [f"# Goal Report: {goal.original}", "", f"Strategy: {rec['strategy']}", f"Reason: {rec['reason']}", "", "## Ranked candidates"]
    for r in rec["ranked"]:
        lines.append(f"- {r['path']}: goal_score={r['goal_score']}")
    return "\n".join(lines)
