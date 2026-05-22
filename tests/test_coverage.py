from empyrical.coverage import coverage_curve


def test_coverage_monotonic_and_ends_at_one(freq_list):
    curve = coverage_curve(freq_list)
    fractions = [c for _, c in curve]
    assert all(b >= a for a, b in zip(fractions, fractions[1:]))
    assert fractions[-1] == 1.0


def test_coverage_exact_values(freq_list):
    curve = coverage_curve(freq_list)
    # total tokens = 13; cumulative counts at each rank: 4, 7, 9, 11, 13
    assert curve[0] == (1, 4 / 13)
    assert curve[1] == (2, 7 / 13)
    assert curve[-1] == (5, 1.0)


def test_coverage_empty():
    assert coverage_curve([]) == []
