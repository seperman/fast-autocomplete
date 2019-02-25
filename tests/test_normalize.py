import pytest
from fast_autocomplete.normalize import remove_any_special_character


class TestMisc:

    @pytest.mark.parametrize("name, expected_result", [
        ('type-r', 'type-r'),
        ('HONDA and Toyota!', 'honda and toyota'),
        (r'cameron? \#1', 'cameron 1'),
        (r'cameron? \#', 'cameron'),
    ])
    def test_extend_and_repeat(self, name, expected_result):
        result = remove_any_special_character(name)
        assert expected_result == result
