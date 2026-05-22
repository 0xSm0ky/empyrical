from empyrical.hill1t import count_1ts


def _count_1ts_bruteforce(word_freqs, processed):
    """Reference implementation used to cross-check the difference-array version."""
    out = {}
    for i in range(len(word_freqs)):
        known = {w for w, _ in word_freqs[:i]}
        out[i] = sum(1 for s in processed if len({w for w in s if w not in known}) == 1)
    return out


def test_count_1ts_exact_values(processed, freq_list):
    counts = count_1ts(freq_list, processed)
    # Computed by hand from the fixture; see tests/conftest.py.
    assert counts == {0: 1, 1: 3, 2: 2, 3: 4, 4: 2}


def test_count_1ts_matches_bruteforce(processed, freq_list):
    assert count_1ts(freq_list, processed) == _count_1ts_bruteforce(freq_list, processed)


def test_count_1ts_at_zero_equals_singleton_sentences(processed, freq_list):
    # With nothing known, only sentences whose distinct-lemma set has size 1 are 1T.
    singleton_sents = sum(1 for s in processed if len(set(s)) == 1)
    assert count_1ts(freq_list, processed)[0] == singleton_sents


def test_count_1ts_handles_empty():
    assert count_1ts([], []) == {}
