# Read-Only Evidence Source Discovery Report

Discovery only. No raw content read. No source modifications.

## Candidate sources

| Source | Path | Format | Schema/Counts | Evidence capability | Limitations |
|--------|------|--------|---------------|---------------------|-------------|
| Hermes default state.db | C:/Users/Jan/.hermes/state.db | SQLite | v23, 0 sessions, 0 messages | None (empty) | No data |
| Hermes profile (jan) state.db | C:/Users/Jan/AppData/Local/hermes/state.db | SQLite | v30, 211 sessions, 36944 messages | Rich (sessions+messages) | Schema v30 unsupported by reader (v23); different profile; not authorized for live access |
| Hermes session-a state.db | C:/Users/Jan/.hermes-session-a/state.db | SQLite | v23, 3 sessions, 449 messages | Rich | Separate profile; not authorized |
| Hermes session-b state.db | C:/Users/Jan/.hermes-session-b/state.db | SQLite | v23, 0 sessions | None | Empty |
| Hermes test-clean state.db | C:/Users/Jan/.hermes-test-clean/state.db | SQLite | v23, 1 session, 2 messages | Minimal | Test fixture, not production evidence |
| Request dumps | C:/Users/Jan/AppData/Local/hermes/profiles/jan/sessions/ | JSON | 289 files, 252 distinct session_ids | API error records only | No successful execution; incomplete |
| AppData sessions dir | C:/Users/Jan/AppData/Local/hermes/sessions/ | JSON (6 files) | not inspected | Unknown | Not inspected |
| test-clean sessions dir | C:/Users/Jan/.hermes-test-clean/sessions/ | JSON (2 files) | not inspected | Unknown | Not inspected |

## Logs (metadata only)
- agent.log, errors.log, gateway.log, audit.jsonl, governance_audit.jsonl, pmos_audit.jsonl present in multiple profiles. Contents not inspected. These may contain operational evidence but include potential secrets; redaction required before use.

## Correlation
- state.db sessions.id correlates with messages.session_id (FK). Request dumps carry session_id but no reliable correlation to state.db without explicit join (not performed).
- No evidence of skill-invocation or tool-result tables in any schema.

## Conclusion
The only non-empty, schema-v23-compatible sources are session-a (3 sessions) and test-clean (1 session). The largest source (AppData profile state.db, v30) is unsupported. The authorized default DB is empty. Request dumps are API-error records only.

No live analysis is recommended without explicit authorization of a specific non-empty source and schema-version support. Real publication remains disabled.
