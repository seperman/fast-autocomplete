import pytest
from fast_autocomplete.normalize import remove_any_special_character, normalize_node_name


class TestMisc:

    @pytest.mark.parametrize("name, expected_result", [
        ('type-r', 'type-r'),
        ('HONDA and Toyota!', 'honda and toyota'),
        (r'bmw? \#1', 'bmw 1'),
        (r'bmw? \#', 'bmw'),
        (None, ''),
    ])
    def test_remove_any_special_character(self, name, expected_result):
        result = remove_any_special_character(name)
        assert expected_result == result

    @pytest.mark.parametrize("name, extra_chars, expected_result", [
        ('type-r', None, 'type r'),
        ('HONDA and Toyota!', None, 'honda and toyota'),
        (r'bmw? \#1', None, 'bmw 1'),
        (r'bmw? \#', None, 'bmw'),
        (r'bmw? \#', {'#'}, 'bmw #'),
        (None, None, ''),
    ])
    def test_normalize_node_name(self, name, extra_chars, expected_result):
        result = normalize_node_name(name, extra_chars=extra_chars)
        assert expected_result == result
