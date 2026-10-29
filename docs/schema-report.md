# Hermes state.db Schema Report (read-only inspection)

- **Path:** C:/Users/Jan/.hermes/state.db
- **Access mode:** `file:...?mode=ro`, `PRAGMA query_only=ON` — succeeded, no errors.
- **Contents read:** metadata only (`sqlite_master`, `PRAGMA table_info`). No row data selected.
- **Relevant tables:** `sessions` (id, source, started_at, ended_at, message_count, ...), `messages` (id, session_id, role, content, timestamp, ...).
- **FTS/virtual tables:** messages_fts*, messages_fts_trigram* — derived indexes, not primary source.
- **WAL sidecars:** state.db-wal, state.db-shm present at inspection time (concurrent writer possible).
- **Authorization:** user-authorized read-only schema inspection only. No adapter implemented yet.
- **Schema version:** 23
- **sessions PK:** `id` (sqlite autoindex); self-FK `parent_session_id` → `sessions.id` (lineage).
- **messages FK:** `session_id` → `sessions.id`.
- **History semantics:** `messages.active` and `messages.compacted` flags; `sessions.archived`, `sessions.pinned`, `sessions.parent_session_id`. Adapter must filter `active=1` and not merge parent/child sessions.
- **FTS tables excluded from initial adapter.**
