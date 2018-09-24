import pytest
from deepdiff import DeepDiff
from fast_autocomplete.lfucache import LFUCache


class TestLFUcache:

    @pytest.mark.parametrize("items, size, expected_results", [
        (['a', 'a', 'b', 'a', 'c', 'b', 'd'], 3, [('a', 2), ('b', 1), ('d', 0)]),
        (['a', 'a', 'b', 'a', 'c', 'b', 'd', 'e', 'c', 'b'], 3, [('a', 2), ('b', 2), ('c', 0)]),
        (['a', 'a', 'b', 'a', 'c', 'b', 'd', 'e', 'c', 'b', 'b', 'c', 'd', 'b'], 3, [('b', 4), ('a', 2), ('d', 0)]),
    ])
    def test_autocomplete(self, items, size, expected_results):
        lfucache = LFUCache(size)
        for item in items:
            lfucache.set(item, f'{item}_cached')
        results = lfucache.get_sorted_cache_keys()
        diff = DeepDiff(expected_results, results)
        assert not diff
