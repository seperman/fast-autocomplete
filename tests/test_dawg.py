import pytest

from fast_autocomplete.dwg import _DawgNode

@pytest.mark.parametrize(
    'node, expected', [
    (None, 0),
    ([], 0)
])
def test_node_count_getter(node, expected):
    assert _DawgNode.node_count_getter(node) == expected
