"""Candidate ranking for eLedger program maturity loop."""

from typing import List, Dict, Any


def score_candidate(proj: Dict[str, Any]) -> float:
    """Score a project (0-100). Higher = better next experiment."""
    score = 0.0
    if proj.get("has_tests"):
        score += 30
    manifests = proj.get("manifests", [])
    if manifests:
        score += 20
    # evidence quality: more files/docs -> small bonus
    score += min(len(proj.get("files", [])), 10)
    # uncertainty penalty for unknown type
    if not manifests:
        score -= 10
    return max(0.0, min(100.0, score))


def rank_candidates(inventory_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ranked = []
    for p in inventory_results:
        ranked.append({**p, "score": score_candidate(p)})
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked
