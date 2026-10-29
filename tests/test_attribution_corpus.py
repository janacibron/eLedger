from eledger.attribution import attribute_skill_evidence


def _classify(text):
    msgs = [{"role": "user", "content": text}]
    return attribute_skill_evidence(msgs)


def test_attribution_corpus_exact():
    cases = [
        ("we used systematic-debugging skill", "mention"),
        ("ran the skill and it passed", "mention"),
        ("result confirmed by evidence", "unknown"),
        ("maybe try debugging", "unknown"),
        ("unrelated chatter", "unknown"),
    ]
    for text, expected in cases:
        got = _classify(text)
        assert got == expected, f"{text!r}: expected {expected}, got {got}"
