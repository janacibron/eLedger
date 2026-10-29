# Security

- Sensitive session data is read-only by default; never commit raw transcripts or credentials.
- Secrets: use environment variables; never commit tokens/keys.
- Read-only source boundaries: source sessions and installed skills are not modified automatically.
- Evidence and audit artifacts must be redacted before publication.
- Report vulnerabilities privately; do not publish exploit details.
