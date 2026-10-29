"""End-to-end pipeline orchestration for eLedger."""
import json
from datetime import datetime, timezone
from pathlib import Path
from .models import RunManifest, Candidate, Evidence
from .ingestion import normalize_session
from .evidence import classify_evidence, build_evidence, build_candidate
from .evaluation import evaluate_candidate
from .audit import write_manifest, hash_file


TRIGGER_TERMS = {
    "systematic-debugging": ["systematic debugging", "root cause", "hypothesis"],
    "test-driven-development": ["test driven development", "red green", "TDD"],
}


def run_pipeline(records, run_id, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # normalize
    sessions = []
    failures = []
    for r in records:
        try:
            sessions.append(normalize_session(r))
        except Exception as e:
            failures.append(str(e))
    # evidence extraction
    evidences = []
    eid = 0
    for ns in sessions:
        for sk, terms in TRIGGER_TERMS.items():
            hits = []
            for m in ns.messages:
                low = (m.content or "").lower()
                if any(t in low for t in terms):
                    hits.append(m.message_id)
            if hits:
                eid += 1
                # classification: unknown by default (no explicit invocation signal)
                cls = "inferred" if len(hits) >= 1 else "unknown"
                ev = build_evidence(
                    eid=f"ev-{eid}", session_id=ns.meta.session_id, message_ids=hits,
                    classification=cls, grade="C", observation=f"topic match for {sk}",
                    quote=" ".join((m.content or "")[:80] for m in ns.messages if m.message_id in hits)[:200],
                )
                evidences.append((sk, ev))
    # candidate generation
    candidates = []
    cid = 0
    for sk in set(s for s, _ in evidences):
        sk_evs = [e for s, e in evidences if s == sk]
        sess_with = set(e.session_id for e in sk_evs)
        cid += 1
        c = build_candidate(
            cid=f"cand-{cid}", title=f"Improve {sk}", skill_id=sk, skill_version="1.0.0",
            evidence_ids=[e.evidence_id for e in sk_evs],
            recurrence_count=len(sess_with), recurrence_denominator=len(sessions),
            classification="inferred", grade="C",
        )
        c.validate()
        candidates.append(c)
    # evaluation
    evals = []
    for c in candidates:
        c_evs = [e for s, e in evidences if s == c.skill_id]
        r = evaluate_candidate(c, c_evs)
        c.disposition = r.disposition
        c.recommendation = "INSUFFICIENT_EVIDENCE" if r.disposition == "insufficient_evidence" else "PROPOSE"
        evals.append(r)
    # report
    report = {
        "run_id": run_id,
        "sessions_in_window": len(sessions) + len(failures),
        "sessions_examined": len(sessions),
        "sessions_excluded": len(failures),
        "retrieval_failures": failures,
        "candidates": [c.to_dict() for c in candidates],
        "evaluations": [e.to_dict() for e in evals],
    }
    from .redaction import redact
    report = redact(report)
    report_path = out_dir / f"{run_id}.json"
    if report_path.exists():
        raise FileExistsError("refusing to overwrite report")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    # audit manifest
    manifest = RunManifest(
        run_id=run_id,
        started_at=datetime.now(timezone.utc).isoformat(),
        completed_at=datetime.now(timezone.utc).isoformat(),
        window_start=None, window_end=None,
        source_scope="synthetic",
        sessions_in_window=len(sessions) + len(failures),
        sessions_examined=len(sessions),
        sessions_excluded=len(failures),
        retrieval_failures=failures,
        candidate_count=len(candidates),
        artifact_hashes={report_path.name: hash_file(report_path)},
        status="complete",
        limitations=["synthetic data only"],
    )
    manifest.validate()
    manifest_path = out_dir / f"{run_id}-manifest.json"
    if manifest_path.exists():
        raise FileExistsError("refusing to overwrite manifest")
    write_manifest(manifest, manifest_path)
    return {"report": str(report_path), "manifest": str(manifest_path), "candidates": len(candidates)}
