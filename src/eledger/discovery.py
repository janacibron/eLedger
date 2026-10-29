"""Read-only directory discovery for eLedger program maturity loop."""

import os
from pathlib import Path
from typing import Dict, List, Any


MANIFESTS = {"pyproject.toml", "package.json", "Cargo.toml", "go.mod", "pom.xml", "build.gradle"}
TEST_DIRS = {"tests", "test", "spec", "__tests__"}


def inventory(root: str, max_depth: int = 3) -> List[Dict[str, Any]]:
    """Read-only inventory of eligible projects under root. Does not execute anything."""
    root_path = Path(root).resolve()
    results = []
    if not root_path.is_dir():
        return results
    for dirpath, dirnames, filenames in os.walk(root_path):
        rel = Path(dirpath).relative_to(root_path)
        depth = len(rel.parts)
        if depth > max_depth:
            dirnames[:] = []
            continue
        # skip hidden and common excluded dirs
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in {"node_modules", "__pycache__", ".git", "venv", ".venv"}]
        manifests = [f for f in filenames if f in MANIFESTS]
        if manifests or (depth > 0 and any(d in dirnames for d in TEST_DIRS)):
            # treat as project if has manifest or tests
            if manifests or any(Path(dirpath, t).is_dir() for t in TEST_DIRS):
                results.append({
                    "path": str(rel) if str(rel) != "." else ".",
                    "manifests": manifests,
                    "has_tests": any(Path(dirpath, t).is_dir() for t in TEST_DIRS),
                    "files": sorted(filenames)[:20],
                })
    return results


def detect_project_type(manifests: List[str]) -> str:
    if "pyproject.toml" in manifests:
        return "python"
    if "package.json" in manifests:
        return "node"
    if "Cargo.toml" in manifests:
        return "rust"
    if "go.mod" in manifests:
        return "go"
    return "unknown"
