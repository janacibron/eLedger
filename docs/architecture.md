# Architecture

## Stages (planned, not yet implemented)

1. Session source adapters — read-only access to platform-specific session stores.
2. Session normalization — convert to common schema.
3. Evidence extraction and provenance — identify candidate signals with traceable refs.
4. Candidate construction — build candidate records with classifications.
5. Evaluation and validation — test against acceptance criteria and regression checks.
6. Human authorization — review and approve/reject.
7. Audit publication — persist sanitized manifests and artifact hashes.

## Principles
- LLM/framework-agnostic core.
- Explicit adapters for platform-specific formats.
- Minimal coupling between analysis and publication.
- Read-only source access by default.
- No automatic skill promotion or change application.
- Evidence provenance and reproducibility.
- Redaction and validation before publication.
- Human authorization for consequential changes.

## Status
Architecture established by this milestone. No session adapter or evidence model implemented yet.
