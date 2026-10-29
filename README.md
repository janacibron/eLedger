# eLedger — Evidence-Driven Evolution & Audit Ledger

> Every change has evidence. Every decision leaves a trail.

LLM-agnostic system that analyzes accessible session histories, identifies improvement opportunities, evaluates evidence, and maintains an auditable record of findings, decisions, tests, and approved changes.

## Project overview and vision

eLedger is a read-only, evidence-first analysis tool. It mines accessible session histories for signals that installed skills or workflows could be improved, correlates those signals to instruction text, grades the evidence, and produces reviewable candidate proposals. It never modifies source sessions, installed skills, registries, or configuration automatically. Every proposal requires explicit human authorization before any change is applied.

The vision is an auditable evolution loop: observe real usage, extract candidate improvements, evaluate them against representative cases, and leave a durable trail of what was found, what was decided, and why.

## LLM-agnostic design

eLedger is designed to be LLM-agnostic. Session access is provided through extensible session adapters rather than a single model or provider. Adapters normalize heterogeneous session stores into a common evidence schema. The analysis, classification, and reporting layers operate on that normalized schema and do not depend on a specific model. (Planned capability — adapter interface not yet implemented.)

## Intended workflow

1. Session ingestion — read session history through a read-only adapter.
2. Normalization — convert sessions into a common message and metadata schema.
3. Evidence extraction — identify candidate signals (corrections, praise, skipped steps, recurring successes, ambiguities, conflicts).
4. Candidate evaluation — grade evidence (A/B/C), deduplicate incidents, account for counter-evidence.
5. Validation — run representative and regression checks against proposed changes.
6. Human approval — a human reviews and authorizes or rejects each candidate.
7. Audit publication — record findings, decisions, tests, and approved changes in an auditable ledger.

(Planned capabilities — none of these stages are implemented yet in this repository.)

## Evidence classifications

- **Confirmed** — direct evidence explicitly establishes the skill's involvement or the relevant action.
- **Inferred** — session behavior is consistent with a skill, but explicit invocation or causal attribution is not established.
- **Unknown** — available evidence is insufficient to determine the relationship.

Topic similarity alone never establishes skill invocation or causal attribution.

## Privacy, read-only source boundaries, and human authorization

- Source session data is read-only. No sessions, messages, databases, WAL, or SHM files are modified.
- No installed skills, registry entries, or configuration are modified automatically.
- Credentials, tokens, and personal or client data are redacted from persisted evidence.
- Every candidate carries traceable session and message references.
- Only a human-authorized, separately scoped operation may modify an installed skill. Candidate approval is not permission to edit or deploy.

## Initial project status and roadmap

**Status:** Initialized. No implementation exists in this repository yet.

**Roadmap (planned):**
- Define the session adapter interface and a first read-only adapter.
- Implement normalization and evidence extraction.
- Implement candidate evaluation, grading, and audit reporting.
- Add synthetic fixtures and tests.
- Add a human-review and authorization flow.

Planned capabilities are distinguished from implemented functionality throughout this document. No benchmarks, supported integrations, APIs, installation instructions, or license terms are claimed at this time.
