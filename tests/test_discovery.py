import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from eledger.discovery import inventory, detect_project_type


def test_inventory_finds_project(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "pyproject.toml").write_text("[project]\nname='x'")
    (proj / "tests").mkdir()
    (proj / "tests" / "t.py").write_text("pass")
    res = inventory(str(tmp_path))
    assert any(r["path"] == "proj" for r in res)
    p = [r for r in res if r["path"] == "proj"][0]
    assert "pyproject.toml" in p["manifests"]
    assert p["has_tests"] is True


def test_detect_project_type():
    assert detect_project_type(["pyproject.toml"]) == "python"
    assert detect_project_type(["package.json"]) == "node"
    assert detect_project_type([]) == "unknown"