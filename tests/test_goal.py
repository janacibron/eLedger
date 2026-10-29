import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from eledger.goal import Goal, rank_for_goal, goal_match_score


def test_goal_match_keyword():
    g = Goal(original="management tool")
    score = goal_match_score(g, {"path": "mgmt", "files": ["management.py"], "manifests": []})
    assert score > 0


def test_rank_for_goal_differentiates():
    g = Goal(original="management tool")
    progs = [
        {"path": "mgmt", "files": ["management.py"], "manifests": []},
        {"path": "calc", "files": ["calc.py"], "manifests": []},
    ]
    ranked = rank_for_goal(g, progs)
    assert ranked[0]["path"] == "mgmt"


def test_goal_preserves_original():
    g = Goal(original="I need a management tool")
    assert g.original == "I need a management tool"