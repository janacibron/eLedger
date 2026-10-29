"""CLI exit code tests."""
import json, tempfile, os, subprocess, sys
from eledger.cli import main

def test_cli_success(tmp_path):
    p = tmp_path / "in.json"
    p.write_text(json.dumps([{"meta":{"session_id":"s1","source":"t"},"messages":[{"id":1,"role":"user","content":"hi"}]}]))
    assert main(["run", str(p), "--output", str(tmp_path/"out.json")]) == 0

def test_cli_incomplete(tmp_path):
    p = tmp_path / "in.json"
    p.write_text(json.dumps([{"meta":{"session_id":"s1","source":"t"},"messages":[{"id":1,"role":"user","content":"hi"}]}, "bad"]))
    assert main(["run", str(p), "--output", str(tmp_path/"out.json")]) == 1

def test_cli_input_error(tmp_path):
    assert main(["run", str(tmp_path/"nope.json")]) == 2

def test_cli_no_args():
    assert main([]) == 2


def test_cli_fatal(tmp_path):
    # IsADirectoryError is not in the caught input-error tuple -> fatal -> 3
    d = tmp_path / "adir"
    d.mkdir()
    assert main(["run", str(d)]) == 3
