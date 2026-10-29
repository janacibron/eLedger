# eLedger Acceptance Matrix

Against the master mandate. Status legend: PASS = implemented + tested/verified; PARTIAL = implemented with known limits; NOT IMPLEMENTED = planned; NOT VERIFIED = claimed but not demonstrated.

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | Read-only source access (no mutation of source sessions) | PASS | `SyntheticSessionReader` is read-only (`is_readonly()`); pipeline never writes source; tests in `test_adapters.py` |
| 2 | Normalization of raw sessions into canonical records | PASS | `ingestion.normalize_session`; `test_models.py`, `test_pipeline.py` |
| 3 | Evidence classification distinct: confirmed/inferred/unknown | PASS | `classify_evidence`; tests `test_evidence_classification`, `test_topic_similarity_not_invocation` |
| 4 | Deduplication and recurrence denominators | PASS | candidate recurrence_count/denominator; `test_e2e_synthetic` checks denominator == session count |
| 5 | Provenance preserved through pipeline | PARTIAL | `NormalizedSession.provenance` stored; not yet asserted in pipeline tests |
| 6 | Counter-evidence / retrieval failures tracked | PASS | `retrieval_failures` in report + manifest; `test_e2e_malformed_record` |
| 7 | Redaction before persistent output | NOT VERIFIED | No explicit redaction routine implemented or tested; quote truncation only |
| 8 | Incomplete runs cannot be reported successful | PASS | manifest status gate; `test_publisher_rejects_incomplete_manifest` |
| 9 | CLI exit codes reflect success/failure | PARTIAL | `main()` returns 0 on success paths; no non-zero exit on failure paths tested |
| 10 | Audit manifest validates and is reproducible | PASS | `RunManifest.validate`, `write_manifest` no-overwrite; `test_run_manifest_no_overwrite` |
| 11 | Publisher allowlist staging | PASS | `Publisher.stage`; `test_publisher_dry_run` |
| 12 | Prohibited file rejection | PASS | `PROHIBITED_EXTENSIONS`, `PROHIBITED_NAMES`; `test_publisher_rejects_prohibited` |
| 13 | Secret scanning | PARTIAL | regex patterns; adversarial test only covers one pattern; bypass not exhaustively tested |
| 14 | Path traversal / symlink safety | PARTIAL | checks present; symlink test skipped on Windows (unverified on this host) |
| 15 | Tampered artifact rejection | PASS | hash mismatch; integrated test confirms |
| 16 | Remote divergence detection | PARTIAL | implemented; not exercised in tests (no real remote) |
| 17 | Dry-run mode | PASS | `dry_run=True` default; `test_publisher_dry_run` |
| 18 | Force-push prevention | PASS | only `git push origin branch`, no force flag |
| 19 | Human authorization boundary (no auto-publish) | PASS | real publication disabled by default; no auto-commit in pipeline |
| 20 | Synthetic-only test suite (no network/creds) | PASS | all tests use temp/local git; no network |
| 21 | Real session adapters | NOT IMPLEMENTED | only `SyntheticSessionReader` |
| 22 | Real GitHub publication | NOT IMPLEMENTED | dry-run only; disabled by default |
| 23 | Redaction routine | NOT IMPLEMENTED | no dedicated redaction module |
| 24 | CLI failure exit codes | NOT IMPLEMENTED | failure paths return 0 or raise |

## Summary
- PASS: 14
- PARTIAL: 5
- NOT IMPLEMENTED: 3
- NOT VERIFIED: 1 (redaction)

## Recommended path
Path 2 (controlled live-integration) is blocked until items 7, 9, 13, 14, 16, 23 are resolved or explicitly scoped. Foundational blockers: redaction (7/23), CLI exit codes (9/24).
