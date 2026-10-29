"""Evidence attribution for skill/tool usage."""
from typing import List, Dict, Any

MENTION_TERMS = ["skill", "tool"]
INVOCATION_TERMS = ["invoke", "run", "execute", "call", "use tool", "please run"]
EXECUTION_TERMS = ["executed", "ran", "tool result", "result:", "output:", "exit code"]
RESULT_TERMS = ["result:", "output:", "exit code", "returned", "completed successfully"]
CONTRADICTION_TERMS = ["failed", "error", "not executed", "did not run"]


def _text(m):
    c = m.get("content")
    return c if isinstance(c, str) else ("" if c is None else str(c))


def _is_invocation(m):
    t = _text(m).lower()
    if m.get("role") != "user":
        return False
    return any(term in t for term in INVOCATION_TERMS)


def _is_execution(m):
    t = _text(m).lower()
    role = m.get("role")
    return role in ("tool", "assistant") and any(term in t for term in EXECUTION_TERMS)


def _is_result(m):
    t = _text(m).lower()
    return any(term in t for term in RESULT_TERMS)


def attribute_skill_evidence(messages: List[Dict[str, Any]]) -> str:
    """Classify evidence state from a list of messages. Returns one of:
    unknown, mention, invocation_request, execution_record, result_with_evidence.
    Linkage rules: result must be linkable (1:1) to an invocation.
    """
    if not messages:
        return "unknown"

    has_mention = any(
        any(term in _text(m).lower() for term in MENTION_TERMS) for m in messages
    )

    invocations = [m for m in messages if _is_invocation(m)]
    executions = [m for m in messages if _is_execution(m)]
    results = [m for m in messages if _is_result(m)]

    contradictory = False
    for m in messages:
        t = _text(m).lower()
        if any(term in t for term in CONTRADICTION_TERMS):
            if results or executions:
                contradictory = True
    if contradictory:
        return "unknown"

    if not invocations and not executions and not results:
        return "mention" if has_mention else "unknown"

    if not executions:
        if invocations:
            return "invocation_request"
        return "mention" if has_mention else "unknown"

    if not results:
        return "execution_record"

    if len(invocations) == 1 and len(results) == 1:
        inv_idx = messages.index(invocations[0])
        res_idx = messages.index(results[0])
        if res_idx > inv_idx:
            return "result_with_evidence"
        return "unknown"
    return "unknown"
