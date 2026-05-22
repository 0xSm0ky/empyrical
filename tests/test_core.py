from empyrical.core import get_freq_list, load_cache, save_cache


def test_freq_list_order_and_tiebreak(processed, freq_list):
    assert get_freq_list(processed) == freq_list


def test_freq_list_empty():
    assert get_freq_list([]) == []


def test_cache_roundtrip(tmp_path, processed):
    path = tmp_path / "cache.json"
    save_cache(str(path), processed)
    assert load_cache(str(path)) == processed


def test_load_cache_rejects_bad_shape(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"not": "a list"}', encoding="utf-8")
    import pytest
    with pytest.raises(ValueError):
        load_cache(str(path))
