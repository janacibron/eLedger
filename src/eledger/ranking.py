"""Candidate ranking for eLedger program maturity loop."""

from typing import List, Dict, Any


def score_candidate(proj: Dict[str, Any]) -> float:
    score = 0.0
    if proj.get("has_tests"):
        score += 30
    manifests = proj.get("manifests", [])
    if manifests:
        score += 20
    score += min(len(proj.get("files", [])), 10)
    if not manifests:
        score -= 10
    return max(0.0, min(100.0, score))


def rank_candidates(inventory_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ranked = []
    for p in inventory_results:
        ranked.append({**p, "score": score_candidate(p)})
    ranked.sort(key=lambda x: (-x["score"], x.get("path", "")))
    return ranked


def detect_type(manifests):
    if "pyproject.toml" in manifests:
        return "python"
    if "package.json" in manifests:
        return "node"
    if "Cargo.toml" in manifests:
        return "rust"
    if "go.mod" in manifests:
        return "go"
    return "unknown"


def ranked_report(inventory_results: List[Dict[str, Any]]) -> str:
    ranked = rank_candidates(inventory_results)
    lines = ["# Candidate Ranking Report", "", f"Total candidates: {len(ranked)}", ""]
    for i, r in enumerate(ranked, 1):
        lines.append(f"## {i}. {r.get('path')}")
        lines.append(f"- Score: {r['score']}")
        lines.append(f"- Project type: {detect_type(r.get('manifests', []))}")
        lines.append(f"- Has tests: {r.get('has_tests')}")
        lines.append(f"- Manifests: {', '.join(r.get('manifests', [])) or 'none'}")
        lines.append(f"- Missing evidence: {'manifests' if not r.get('manifests') else 'none obvious'}")
        lines.append("")
    return "\n".join(lines)
