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

## Publisher timeout semantics (Batch 1)

- `git fetch` / `git rev-list`: 10s timeout → treated as divergence (fail-closed).
- `git add` (stage): 10s timeout → stage fails with "outcome unknown".
- `git commit`: 30s timeout → status `commit_timeout` (outcome unknown).
- `git push`: 30s timeout → status `push_timeout` (outcome unknown).

Timeout outcomes are NOT confirmed failures. The remote may have accepted the operation before the local process terminated. Operator must verify repository/remote state before retrying. No automatic retry or rerun of the pipeline is performed. Real publication remains disabled by default (dry_run=True).
