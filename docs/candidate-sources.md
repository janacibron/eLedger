# Candidate Session Sources (discovery only — no authorization implied)

Discovered by filesystem listing only. No session contents were read. No source is authorized for eLedger by default.

| Source | Path | Format | Read-only evidence |
|--------|------|--------|--------------------|
| Hermes default state.db | C:/Users/Jan/.hermes/state.db | SQLite | File readable; WAL sidecars present (state.db-wal, state.db-shm) — concurrent writer may exist |
| Hermes profile state.db (jan) | C:/Users/Jan/AppData/Local/hermes/state.db | SQLite | Same as above |
| Hermes profile sessions dir | C:/Users/Jan/AppData/Local/hermes/sessions/ | directory | Contents not inspected |
| Hermes default sessions dir | C:/Users/Jan/.hermes/sessions/ | directory | Contents not inspected |
| LocalCoder sessions | C:/Users/Jan/.localcoder/sessions/*.jsonl | JSONL | Append-only log files; read-only open possible |
| Claude Code sessions | C:/Users/Jan/.claude/sessions/ | directory | Contents not inspected |

## Notes
- All Hermes state.db files are owned by the Hermes runtime; eLedger must NOT assume authorization.
- WAL sidecars indicate possible concurrent writes; a read-only adapter must open with `mode=ro` or copy to scratch.
- No live adapter should be implemented until the user explicitly designates one source and confirms read-only access.
- Real GitHub publication remains disabled.
