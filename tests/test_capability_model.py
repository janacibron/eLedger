import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from eledger.capability_model import all_capabilities, status_counts, get_capability


def test_capability_model_loads():
    caps = all_capabilities()
    assert len(caps) == 10
    assert status_counts()["PASS"] == 6


def test_capability_lookup():
    c = get_capability("C5")
    assert c is not None
    assert c.status == "PARTIAL"
