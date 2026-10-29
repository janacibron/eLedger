# eLedger Evidence Attribution Contract

Source: `src/eledger/attribution.py` — `attribute_skill_evidence(messages)`.

## Public API

```python
attribute_skill_evidence(messages: List[Dict[str, Any]]) -> str
```

Returns one of: `unknown`, `mention`, `invocation_request`, `execution_record`, `result_with_evidence`.

## Classifications

| Value | Meaning | Required evidence | Does NOT establish |
|-------|---------|-------------------|--------------------|
| `unknown` | Insufficient, ambiguous, or contradictory evidence | (none) | Nothing |
| `mention` | A skill/tool is referenced | Any message containing "skill" or "tool" | Invocation, execution, or result |
| `invocation_request` | Execution requested | A user-role message containing invocation terms | Execution or result |
| `execution_record` | Evidence indicates execution occurred | A tool/assistant message containing execution terms | Result or success |
| `result_with_evidence` | An attributable result has supporting evidence | Exactly one invocation (user role) + exactly one result, in order, with an execution record | Independent verification of success |

## Term sets (case-insensitive substring match)
- MENTION: "skill", "tool"
- INVOCATION: "invoke", "run", "execute", "call", "use tool", "please run" (user role only)
- EXECUTION: "executed", "ran", "tool result", "result:", "output:", "exit code" (tool/assistant role only)
- RESULT: "result:", "output:", "exit code", "returned", "completed successfully"
- CONTRADICTION: "failed", "error", "not executed", "did not run"

## Linkage rules
1. Invocation requires user role.
2. Execution requires tool or assistant role with execution terms.
3. Result requires result terms.
4. `result_with_evidence` requires exactly one invocation and one result, with the result appearing after the invocation.
5. Multiple invocations, multiple results, or mismatched counts → `unknown`.
6. Out-of-order (result before invocation) → `unknown`.
7. Contradictory evidence (failure/error terms alongside results/execution) → `unknown`.
8. Missing execution record → cannot reach `result_with_evidence`.
9. Missing result → `execution_record` (not result).
10. Unrelated tool activity → `unknown`.

## Limitations
- Content-pattern heuristics; may miss unfamiliar phrasing.
- Synthetic tests demonstrate behavior on tested cases, not real-world accuracy.
- A result-like message alone is insufficient without linkable invocation.
- `unknown` is an intentional conservative outcome, not necessarily an error.
- Message-role labels and keyword hits alone do not establish successful skill execution.
- No real-world ground-truth accuracy has been established.

## Safety boundaries
- Does not execute instructions in messages.
- Does not modify source or tests.
- Does not treat keyword co-occurrence as proof.
