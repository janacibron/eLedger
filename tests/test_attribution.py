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
    msgs = [{"role":"assistant","content":"executed; result: ok, exit code 0"}]
    assert attribute_skill_evidence(msgs) == "result_with_evidence"

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
