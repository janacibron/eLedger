"""Baseline test: package import and version."""
import eledger


def test_package_importable():
    assert eledger.__version__ == "0.1.0"
