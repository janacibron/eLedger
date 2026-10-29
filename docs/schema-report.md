# Hermes state.db Schema Report (read-only inspection)

- **Path:** C:/Users/Jan/.hermes/state.db
- **Access mode:** `file:...?mode=ro`, `PRAGMA query_only=ON` — succeeded, no errors.
- **Contents read:** metadata only (`sqlite_master`, `PRAGMA table_info`). No row data selected.
- **Relevant tables:** `sessions` (id, source, started_at, ended_at, message_count, ...), `messages` (id, session_id, role, content, timestamp, ...).
- **FTS/virtual tables:** messages_fts*, messages_fts_trigram* — derived indexes, not primary source.
- **WAL sidecars:** state.db-wal, state.db-shm present at inspection time (concurrent writer possible).
- **Authorization:** user-authorized read-only schema inspection only. No adapter implemented yet.
- **Next gate:** review before implementing `HermesStateDbReader`.
