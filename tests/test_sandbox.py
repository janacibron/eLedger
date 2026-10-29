import sys, os, tempfile
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from eledger.sandbox import Sandbox, promote, rollback


def test_sandbox_run_success():
    sb = Sandbox()
    try:
        r = sb.run(["python", "-c", "print('hi')"])
        assert r["returncode"] == 0
        assert "hi" in r["stdout"]
    finally:
        sb.cleanup()


def test_sandbox_run_failure():
    sb = Sandbox()
    try:
        r = sb.run(["python", "-c", "raise SystemExit(1)"])
        assert r["returncode"] == 1
    finally:
        sb.cleanup()


def test_sandbox_timeout():
    sb = Sandbox()
    try:
        r = sb.run(["python", "-c", "import time; time.sleep(10)"], timeout=1)
        assert r["timed_out"] is True
    finally:
        sb.cleanup()


def test_promote_requires_validation():
    d = tempfile.mkdtemp()
    cand = os.path.join(d, "c.txt")
    tgt = os.path.join(d, "t", "c.txt")
    with open(cand, "w") as f:
        f.write("x")
    assert promote(Path(cand), Path(tgt), False)["status"] == "rejected"
    assert not os.path.exists(tgt)
    assert promote(Path(cand), Path(tgt), True)["status"] == "promoted"
    assert os.path.exists(tgt)


def test_promote_no_overwrite_without_backup():
    d = tempfile.mkdtemp()
    cand = os.path.join(d, "c.txt")
    tgt = os.path.join(d, "t", "c.txt")
    os.makedirs(os.path.dirname(tgt))
    with open(cand, "w") as f:
        f.write("x")
    with open(tgt, "w") as f:
        f.write("old")
    r = promote(Path(cand), Path(tgt), True, backup=False)
    assert r["status"] == "rejected"
    assert r["reason"] == "target exists (no-overwrite)"


def test_rollback():
    d = tempfile.mkdtemp()
    cand = os.path.join(d, "c.txt")
    tgt = os.path.join(d, "t", "c.txt")
    os.makedirs(os.path.dirname(tgt))
    with open(cand, "w") as f:
        f.write("new")
    with open(tgt, "w") as f:
        f.write("old")
    r = promote(Path(cand), Path(tgt), True)
    assert r["status"] == "promoted"
    assert rollback(Path(tgt))["status"] == "rolled_back"
    assert open(tgt).read() == "old"
