"""HermesStateDbReader synthetic tests."""
import sqlite3, tempfile, os
import pytest
from eledger.hermes_reader import HermesStateDbReader, SchemaError


def make_db(path, version=23, include_fk=True):
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
        content TEXT, timestamp REAL NOT NULL, active INTEGER NOT NULL, compacted INTEGER NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    )""")
    # seed
    conn.execute("INSERT INTO sessions VALUES ('s1','hermes',1.0,2.0,2,NULL,0,0)")
    conn.execute("INSERT INTO sessions VALUES ('s2','hermes',3.0,4.0,1,'s1',1,1)")
    conn.execute("INSERT INTO messages VALUES (1,'s1','user','hi',1.0,1,0)")
    conn.execute("INSERT INTO messages VALUES (2,'s1','assistant','yo',2.0,0,1)")
    conn.execute("INSERT INTO messages VALUES (3,'s1','user','late',1.5,1,0)")
    conn.execute("INSERT INTO messages VALUES (4,'s2','user','child',3.0,1,0)")
    conn.commit()
    conn.close()
    return path


def test_list_and_read(tmp_path):
    db = make_db(str(tmp_path / "t.db"))
    r = HermesStateDbReader(db)
    assert r.list_sessions() == ["s1", "s2"]
    s1 = r.read_session("s1")
    assert s1["meta"]["session_id"] == "s1"
    # only active messages, ordered by timestamp then id
    ids = [m["id"] for m in s1["messages"]]
    assert ids == [1, 3]
    assert s1["meta"]["parent_session_id"] is None
    s2 = r.read_session("s2")
    assert s2["meta"]["parent_session_id"] == "s1"
    assert s2["meta"]["archived"] is True
    assert s2["meta"]["pinned"] is True
    r.close()


def test_schema_version_mismatch(tmp_path):
    db = make_db(str(tmp_path / "t.db"), version=99)
    with pytest.raises(SchemaError):
        HermesStateDbReader(db).list_sessions()


def test_missing_column(tmp_path):
    db = str(tmp_path / "t.db")
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE schema_version (version INTEGER NOT NULL)")
    conn.execute("INSERT INTO schema_version VALUES (23)")
    conn.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY, source TEXT NOT NULL, started_at REAL NOT NULL)")
    conn.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, session_id TEXT NOT NULL, role TEXT NOT NULL, content TEXT, timestamp REAL NOT NULL, active INTEGER NOT NULL, compacted INTEGER NOT NULL)")
    conn.commit(); conn.close()
    with pytest.raises(SchemaError):
        HermesStateDbReader(db).list_sessions()


def test_unknown_session(tmp_path):
    db = make_db(str(tmp_path / "t.db"))
    r = HermesStateDbReader(db)
    with pytest.raises(KeyError):
        r.read_session("nope")
    r.close()

def test_empty_session(tmp_path):
    db = str(tmp_path / "t.db")
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE schema_version (version INTEGER NOT NULL)")
    conn.execute("INSERT INTO schema_version VALUES (23)")
    conn.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY, source TEXT NOT NULL, started_at REAL NOT NULL, ended_at REAL, message_count INTEGER, parent_session_id TEXT, archived INTEGER, pinned INTEGER)")
    conn.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, session_id TEXT NOT NULL, role TEXT NOT NULL, content TEXT, timestamp REAL NOT NULL, active INTEGER NOT NULL, compacted INTEGER NOT NULL, FOREIGN KEY (session_id) REFERENCES sessions(id))")
    conn.execute("INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?)", ("empty","hermes",1.0,None,0,None,0,0))
    conn.commit(); conn.close()
    r = HermesStateDbReader(db)
    s = r.read_session("empty")
    assert s["messages"] == []
    r.close()

def test_readonly_no_mutation(tmp_path):
    db = make_db(str(tmp_path / "t.db"))
    before = os.path.getsize(db)
    r = HermesStateDbReader(db)
    _ = r.read_all()
    r.close()
    after = os.path.getsize(db)
    assert before == after
