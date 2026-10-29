import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from eledger.ranking import rank_candidates, score_candidate


def test_rank_prefers_tests():
    a = {"path": "a", "has_tests": True, "manifests": ["pyproject.toml"], "files": []}
    b = {"path": "b", "has_tests": False, "manifests": [], "files": []}
    ranked = rank_candidates([a, b])
    assert ranked[0]["path"] == "a"


def test_ranked_report():
    from eledger.ranking import ranked_report
    r = ranked_report([{"path": "a", "has_tests": True, "manifests": ["pyproject.toml"], "files": []}])
    assert "Candidate Ranking Report" in r
    assert "## 1. a" in r


def test_score_bounds():
    from eledger.ranking import score_candidate
    s = score_candidate({"path": "x", "has_tests": False, "manifests": [], "files": []})
    assert 0 <= s <= 100


def test_tie_break_by_path():
    from eledger.ranking import rank_candidates
    a = {"path": "b", "has_tests": True, "manifests": ["pyproject.toml"], "files": []}
    b = {"path": "a", "has_tests": True, "manifests": ["pyproject.toml"], "files": []}
    ranked = rank_candidates([a, b])
    assert ranked[0]["path"] == "a"