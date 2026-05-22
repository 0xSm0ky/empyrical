from empyrical.mine import find_1t_sentences


def test_mine_finds_expected(processed):
    results = find_1t_sentences(processed, known={"the"})
    unknowns = [u for u, _ in results]
    # S1, S2, S4 are the 1T sentences when only "the" is known.
    assert unknowns == ["cat", "dog", "fish"]


def test_mine_respects_max_results(processed):
    results = find_1t_sentences(processed, known={"the"}, max_results=1)
    assert len(results) == 1
    assert results[0][0] == "cat"


def test_mine_empty_when_all_known(processed):
    all_lemmas = {w for s in processed for w in s}
    assert find_1t_sentences(processed, known=all_lemmas) == []


def test_mine_returns_sentence_lemmas(processed):
    results = find_1t_sentences(processed, known={"the"})
    # First match should be S1 = ["the", "cat"].
    assert results[0][1] == ["the", "cat"]
