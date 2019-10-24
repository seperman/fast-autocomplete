import os
import pytest
from fast_autocomplete import autocomplete_factory, AutoComplete

current_dir = os.path.dirname(os.path.abspath(__file__))
fixture_dir = os.path.join(current_dir, 'fixtures')

content_files = {
    'words': {
        'filepath': os.path.join(fixture_dir, 'sample_words.json'),
        'compress': True  # means compress the graph data in memory
    }
}

autocomplete = autocomplete_factory(content_files=content_files)


class AutoCompleteIgnoreCount(AutoComplete):
    SHOULD_INCLUDE_COUNT = False


autocomplete_ignore_count = autocomplete_factory(content_files=content_files, module=AutoCompleteIgnoreCount)


class TestLoader:

    @pytest.mark.parametrize('word, expected_result, expected_unsorted_result', [
        ('acu',
         [['acura'], ['acura mdx'], ['acura rdx']],
         [['acura'], ['acura rlx'], ['acura rdx']]),
    ])
    def test_loader(self, word, expected_result, expected_unsorted_result):
        result = autocomplete.search(word=word, size=3)
        assert expected_result == result

        result = autocomplete_ignore_count.search(word=word, size=3)
        assert expected_unsorted_result == result
