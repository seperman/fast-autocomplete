import random
import pytest
import concurrent.futures
from deepdiff import DeepDiff
from fast_autocomplete.lfucache import LFUCache


def threaded_set(cache, key):
    cache.set(key, f'{key}_cached')


def threaded_get(cache, key):
    return cache.get(key)


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

    def test_get_multithreading(self):
        keys = 'aaaaaaaaaaaaaaaaaaaaaaaaaaabbc'
        lfucache = LFUCache(2)

        def key_gen():
            i = 0
            while i < 30000:
                i += 1
                yield random.choice(keys)

        def random_func(cache, key):
            return random.choice([threaded_get, threaded_get, threaded_set])(cache, key)

        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            futures = (executor.submit(random_func, lfucache, key) for key in key_gen())
            for future in concurrent.futures.as_completed(futures):
                future.result()
