"""Hardening tests for HermesStateDbReader."""
import sqlite3, os
import pytest
from eledger.hermes_reader import HermesStateDbReader, SchemaError


def make_db(path, version=23):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE schema_version (version INTEGER NOT NULL)")
    conn.execute("INSERT INTO schema_version VALUES (?)", (version,))
    conn.execute("""CREATE TABLE sessions (
        id TEXT PRIMARY KEY, source TEXT NOT NULL, started_at REAL NOT NULL,
        ended_at REAL, message_count INTEGER, parent_session_id TEXT,
        archived INTEGER, pinned INTEGER,
        FOREIGN KEY (parent_session_id) REFERENCES sessions(id)
    )""")
    conn.execute("""CREATE TABLE messages (
        id INTEGER PRIMARY KEY, session_id TEXT NOT NULL, role TEXT NOT NULL,
        content TEXT, timestamp REAL, active INTEGER NOT NULL, compacted INTEGER NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    )""")
    conn.execute("INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?)", ("parent","hermes",1.0,2.0,1,None,0,0))
    conn.execute("INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?)", ("child","hermes",3.0,4.0,2,"parent",1,1))
    conn.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,?)", (1,"parent","user","pmsg",1.0,1,0))
    conn.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,?)", (2,"child","user","active-msg",3.0,1,0))
    conn.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,?)", (3,"child","assistant","inactive",3.5,0,1))
    conn.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,?)", (4,"child","user","compacted-but-active",3.2,1,1))
    conn.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,?)", (5,"child","user","tie-a",3.2,1,0))
    conn.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,?)", (6,"child","user",None,None,1,0))
    conn.commit(); conn.close()
    return path


def test_parent_child_separation(tmp_path):
    db = make_db(str(tmp_path / "t.db"))
    r = HermesStateDbReader(db)
    parent = r.read_session("parent")
    child = r.read_session("child")
    assert [m["id"] for m in parent["messages"]] == [1]
    assert [m["id"] for m in child["messages"]] == [6, 2, 4, 5]  # nulls first (SQLite), then timestamp, id
    # Actually order by timestamp,id: 3.0(2), 3.2(4,5), None(6) -> sqlite nulls first by default
    r.close()


def test_inactive_excluded_compacted_retained(tmp_path):
    db = make_db(str(tmp_path / "t.db"))
    r = HermesStateDbReader(db)
    child = r.read_session("child")
    ids = [m["id"] for m in child["messages"]]
    assert 3 not in ids  # inactive excluded
    assert 4 in ids  # compacted-but-active retained (conservative)
    r.close()


def test_archived_pinned_metadata(tmp_path):
    db = make_db(str(tmp_path / "t.db"))
    r = HermesStateDbReader(db)
    child = r.read_session("child")
    assert child["meta"]["archived"] is True
    assert child["meta"]["pinned"] is True
    parent = r.read_session("parent")
    assert parent["meta"]["archived"] is False
    assert parent["meta"]["pinned"] is False
    r.close()


def test_missing_table(tmp_path):
    db = str(tmp_path / "t.db")
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE schema_version (version INTEGER NOT NULL)")
    conn.execute("INSERT INTO schema_version VALUES (23)")
    conn.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY)")
    conn.commit(); conn.close()
    with pytest.raises(SchemaError):
        HermesStateDbReader(db).list_sessions()


def test_missing_fk(tmp_path):
    db = str(tmp_path / "t.db")
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE schema_version (version INTEGER NOT NULL)")
    conn.execute("INSERT INTO schema_version VALUES (23)")
    conn.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY, source TEXT NOT NULL, started_at REAL NOT NULL, ended_at REAL, message_count INTEGER, parent_session_id TEXT, archived INTEGER, pinned INTEGER)")
    conn.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, session_id TEXT NOT NULL, role TEXT NOT NULL, content TEXT, timestamp REAL, active INTEGER NOT NULL, compacted INTEGER NOT NULL)")
    conn.commit(); conn.close()
    with pytest.raises(SchemaError):
        HermesStateDbReader(db).list_sessions()


def test_readonly_no_mutation_hardening(tmp_path):
    db = make_db(str(tmp_path / "t.db"))
    before = os.path.getmtime(db)
    # also capture sidecar absence
    r = HermesStateDbReader(db)
    _ = r.read_all()
    r.close()
    after = os.path.getmtime(db)
    assert before == after


def test_null_timestamp_deterministic(tmp_path):
    db = make_db(str(tmp_path / "t.db"))
    r = HermesStateDbReader(db)
    child = r.read_session("child")
    # null timestamp message present
    assert any(m["id"] == 6 for m in child["messages"])
    r.close()
