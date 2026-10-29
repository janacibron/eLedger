"""CLI entry point."""
import argparse, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from eledger.models import SessionMeta, MessageRecord, NormalizedSession
from eledger.ingestion import normalize_session
from eledger.evaluation import evaluate_candidate
from eledger.models import Candidate


def main(argv=None):
    ap = argparse.ArgumentParser(prog="eledger")
    sub = ap.add_subparsers(dest="cmd")
    p_ingest = sub.add_parser("ingest", help="normalize a JSON file of sessions")
    p_ingest.add_argument("input")
    p_ingest.add_argument("--output", default=None)
    p_val = sub.add_parser("validate", help="validate a candidate JSON")
    p_val.add_argument("input")
    p_run = sub.add_parser("run", help="run analysis on a JSON session file")
    p_run.add_argument("input")
    p_run.add_argument("--output", default="report.json")
    args = ap.parse_args(argv)
    if args.cmd == "ingest":
        data = json.load(open(args.input, encoding="utf-8"))
        records = data if isinstance(data, list) else [data]
        out = []
        for r in records:
            try:
                ns = normalize_session(r)
                out.append(ns.meta.session_id)
            except Exception as e:
                out.append({"error": str(e)})
        if args.output:
            with open(args.output, "w") as f:
                json.dump(out, f)
        else:
            print(json.dumps(out))
        return 0
    if args.cmd == "validate":
        data = json.load(open(args.input, encoding="utf-8"))
        print("valid json with", len(data) if isinstance(data, list) else 1, "records")
        return 0
    if args.cmd == "run":
        data = json.load(open(args.input, encoding="utf-8"))
        records = data if isinstance(data, list) else [data]
        sessions = []
        for r in records:
            try:
                sessions.append(normalize_session(r))
            except Exception as e:
                print("skip:", e)
        print(f"normalized {len(sessions)} sessions")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
