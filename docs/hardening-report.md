# HermesStateDbReader Hardening Report

- **Commit base:** ded1d11 + hardening tests
- **Disposition:** CONDITIONALLY VALIDATED

## Verified
- Read-only connection (`mode=ro`, `PRAGMA query_only=ON`); no DB mutation (size/mtime unchanged).
- Schema version 23 enforced; fail-closed on missing tables/columns/FK.
- `active=1` filtering; inactive messages excluded.
- `compacted` retained as metadata but NOT filtered (meaning unverified — conservative).
- Parent/child sessions not merged.
- Archived/pinned metadata preserved.
- Deterministic ordering by timestamp then id (nulls first per SQLite).
- Empty sessions and missing relationships handled.
- No raw session content logged by reader.

## Unresolved
- Semantics of `compacted` flag: not established from authoritative evidence. Conservative: retained, not filtered. Must be verified before using compacted as an exclusion criterion.
- Null timestamp handling: SQLite sorts NULL first; documented but not normalized.

## Authorization
- Live session analysis still requires explicit authorization. Real publication disabled.
