import pytest


@pytest.fixture
def processed():
    """A tiny hand-built corpus with a known frequency profile.

    Lemma counts after this fixture:
        the=4, cat=3, and=2, dog=2, fish=2.
    Sorted freq list (tie-breaking by lemma ascending):
        [(the,4), (cat,3), (and,2), (dog,2), (fish,2)]
    """
    return [
        ["the", "cat"],
        ["the", "dog"],
        ["the", "cat", "and", "dog"],
        ["fish"],
        ["the", "cat", "and", "fish"],
    ]


@pytest.fixture
def freq_list():
    return [("the", 4), ("cat", 3), ("and", 2), ("dog", 2), ("fish", 2)]
