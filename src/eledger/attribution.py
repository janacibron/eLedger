"""Evidence attribution for skill/tool usage."""
from typing import List, Dict, Any

MENTION_TERMS = ["skill", "tool"]
INVOCATION_TERMS = ["invoke", "run", "execute", "call", "use tool", "please run"]
EXECUTION_TERMS = ["executed", "ran", "tool result", "result:", "output:", "exit code"]
RESULT_TERMS = ["result:", "output:", "exit code", "returned", "completed successfully"]


def _text(m):
    c = m.get("content")
    return c if isinstance(c, str) else ("" if c is None else str(c))


def attribute_skill_evidence(messages: List[Dict[str, Any]]) -> str:
    """Classify evidence state from a list of messages. Returns one of:
    unknown, mention, invocation_request, execution_record, result_with_evidence.
    Never infers success from keyword hits alone.
    """
    if not messages:
        return "unknown"
    has_mention = False
    has_invocation = False
    has_execution = False
    has_result = False
    contradictory = False
    # track roles
    for m in messages:
        t = _text(m).lower()
        role = m.get("role")
        if any(term in t for term in MENTION_TERMS):
            has_mention = True
        if any(term in t for term in INVOCATION_TERMS):
            has_invocation = True
        # execution record requires a tool/assistant role recording execution
        if role in ("tool", "assistant") and any(term in t for term in EXECUTION_TERMS):
            has_execution = True
        if any(term in t for term in RESULT_TERMS):
            has_result = True
    # contradictory: invocation request but explicit failure/no result
    for m in messages:
        t = _text(m).lower()
        if "failed" in t or "error" in t or "not executed" in t:
            # if there's also a claim of success/result, contradictory
            if has_result:
                contradictory = True
    if contradictory:
        return "unknown"
    if has_execution and has_result:
        return "result_with_evidence"
    if has_execution:
        return "execution_record"
    if has_invocation:
        return "invocation_request"
    if has_mention:
        return "mention"
    return "unknown"
