"""Evidence attribution tests."""
from eledger.attribution import attribute_skill_evidence

def test_empty_unknown():
    assert attribute_skill_evidence([]) == "unknown"

def test_mention():
    msgs = [{"role":"user","content":"what is the skill for debugging?"}]
    assert attribute_skill_evidence(msgs) == "mention"

def test_invocation_request():
    msgs = [{"role":"user","content":"please run the debug skill"}]
    assert attribute_skill_evidence(msgs) == "invocation_request"

def test_execution_record():
    msgs = [{"role":"assistant","content":"executed the tool"}, {"role":"user","content":"thanks"}]
    assert attribute_skill_evidence(msgs) == "execution_record"

def test_result_with_evidence():
    msgs = [{"role": "assistant", "content": "executed; result: ok, exit code 0"}]
    # no invocation request -> cannot link -> unknown
    assert attribute_skill_evidence(msgs) == "unknown"

def test_missing_result_unknown():
    msgs = [{"role":"assistant","content":"executed the tool"}]
    # execution record present but no result terms -> execution_record, not result
    assert attribute_skill_evidence(msgs) == "execution_record"

def test_ambiguous_tool_role_only():
    msgs = [{"role":"tool","content":"some output"}]
    # no execution terms -> unknown (tool role alone insufficient)
    assert attribute_skill_evidence(msgs) == "unknown"

def test_contradictory_unknown():
    msgs = [{"role":"assistant","content":"executed; result: ok"}, {"role":"assistant","content":"error: failed"}]
    assert attribute_skill_evidence(msgs) == "unknown"

def test_unrelated_tool_activity_unknown():
    msgs = [{"role":"tool","content":"file listing complete"}]
    assert attribute_skill_evidence(msgs) == "unknown"


# --- Synthetic regression matrix ---

def test_reg_mention_only():
    msgs = [{"role": "user", "content": "what skill handles debugging?"}]
    assert attribute_skill_evidence(msgs) == "mention"

def test_reg_invocation_request():
    msgs = [{"role": "user", "content": "please run the debug tool"}]
    assert attribute_skill_evidence(msgs) == "invocation_request"

def test_reg_execution_evidence():
    msgs = [{"role": "assistant", "content": "executed the tool"}]
    assert attribute_skill_evidence(msgs) == "execution_record"

def test_reg_unlinked_result_unknown():
    msgs = [
        {"role": "assistant", "content": "result: ok"},
    ]
    # no invocation -> cannot link
    assert attribute_skill_evidence(msgs) == "unknown"

def test_reg_linked_result():
    msgs = [
        {"role": "user", "content": "please run the tool"},
        {"role": "assistant", "content": "executed; result: ok, exit code 0"},
    ]
    assert attribute_skill_evidence(msgs) == "result_with_evidence"

def test_reg_misleading_success_claim():
    msgs = [{"role": "assistant", "content": "completed successfully"}]
    # no execution evidence -> not a result
    assert attribute_skill_evidence(msgs) in ("unknown", "mention")

def test_reg_paraphrased():
    msgs = [
        {"role": "user", "content": "call the debug skill"},
        {"role": "assistant", "content": "ran it; output: done"},
    ]
    assert attribute_skill_evidence(msgs) == "result_with_evidence"

def test_reg_unrelated_tool_activity():
    msgs = [{"role": "tool", "content": "file listing complete"}]
    assert attribute_skill_evidence(msgs) == "unknown"

def test_reg_missing_result():
    msgs = [
        {"role": "user", "content": "please run the tool"},
        {"role": "assistant", "content": "executed the tool"},
    ]
    assert attribute_skill_evidence(msgs) == "execution_record"

def test_reg_contradictory():
    msgs = [
        {"role": "assistant", "content": "executed; result: ok"},
        {"role": "assistant", "content": "error: failed"},
    ]
    assert attribute_skill_evidence(msgs) == "unknown"

def test_reg_out_of_order():
    msgs = [
        {"role": "assistant", "content": "result: ok, exit code 0"},
        {"role": "user", "content": "please run the tool"},
    ]
    # result before invocation -> cannot link reliably -> unknown
    assert attribute_skill_evidence(msgs) == "unknown"

def test_reg_multiple_invocations():
    msgs = [
        {"role": "user", "content": "please run tool A"},
        {"role": "user", "content": "please run tool B"},
        {"role": "assistant", "content": "executed; result: ok"},
    ]
    # multiple invocations, one result -> cannot attribute -> unknown
    assert attribute_skill_evidence(msgs) == "unknown"
