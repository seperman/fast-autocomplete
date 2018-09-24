import pytest
from fast_autocomplete.misc import _extend_and_repeat


class TestMisc:

    @pytest.mark.parametrize("list1, list2, expected_result", [
        (['a', 'b'], ['c', 'd'], [['a', 'b', 'c'], ['a', 'b', 'd']]),
        (['a', 'b'], ['a', 'd'], [['a', 'b', 'd']]),
        (['a', 'b'], ['b model2', 'd'], [['a', 'b model2'], ['a', 'b', 'd']]),
        ([], ['c', 'd'], [['c'], ['d']]),
    ])
    def test_extend_and_repeat(self, list1, list2, expected_result):
        result = _extend_and_repeat(list1, list2)
        assert expected_result == result
