"""Session adapter contract tests."""
import pytest
from eledger.adapters import SyntheticSessionReader, validate_reader


def test_reader_readonly():
    r = SyntheticSessionReader([{"meta": {"session_id": "s1"}, "messages": []}])
    assert r.is_readonly() is True
    assert validate_reader(r) is True

def test_reader_missing_session_raises():
    r = SyntheticSessionReader([{"meta": {"session_id": "s1"}, "messages": []}])
    with pytest.raises(KeyError):
        r.read_session("nope")

def test_reader_malformed_input_rejected():
    with pytest.raises((TypeError, KeyError, AttributeError)):
        SyntheticSessionReader([{"meta": {"session_id": "s1"}, "messages": []}, "bad"])

def test_reader_list_sessions():
    r = SyntheticSessionReader([{"meta": {"session_id": "s1"}, "messages": []}, {"meta": {"session_id": "s2"}, "messages": []}])
    ids = r.list_sessions("a", "b")
    assert set(ids) == {"s1", "s2"}
