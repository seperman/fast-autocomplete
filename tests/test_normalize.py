import pytest
from fast_autocomplete.normalize import remove_any_special_character


class TestMisc:

    @pytest.mark.parametrize("name, expected_result", [
        ('type-r', 'type-r'),
        ('HONDA and Toyota!', 'honda and toyota'),
        (r'bmw? \#1', 'bmw 1'),
        (r'bmw? \#', 'bmw'),
    ])
    def test_extend_and_repeat(self, name, expected_result):
        result = remove_any_special_character(name)
        assert expected_result == result
