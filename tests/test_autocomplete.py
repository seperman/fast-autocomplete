import os
import csv
import json
import pytest
from typing import NamedTuple

from pprint import pprint
from fast_autocomplete.misc import read_csv_gen
from fast_autocomplete import AutoComplete, DrawGraphMixin
from fast_autocomplete.dawg import FindStep


current_dir = os.path.dirname(os.path.abspath(__file__))

WHAT_TO_PRINT = {'word', 'results', 'expected_results', 'result', 'expected_result',
                 'find_steps', 'expected_steps', 'search_results', 'search_results_immutable'}


class Info(NamedTuple):
    make: 'Info' = None
    model: 'Info' = None
    original_key: 'Info' = None

    def get(self, key, default=None):
        return getattr(self, key, default)

    __get__ = get


def parameterize_cases(cases):
    return [tuple(i.values()) for i in cases]


def print_results(local_vars):
    common = WHAT_TO_PRINT & set(local_vars.keys())
    for key in common:
        print(f'- {key}:')
        pprint(local_vars[key])


def get_words(path):

    file_path = os.path.join(current_dir, path)
    csv_gen = read_csv_gen(file_path, csv_func=csv.DictReader)

    words = {}

    for line in csv_gen:
        make = line['make'].lower()
        model = line['model'].lower()
        if make != model:
            local_words = [model, '{} {}'.format(make, model)]
            while local_words:
                word = local_words.pop()
                if word not in words:
                    words[word] = dict(line)
        if make not in words:
            words[make] = {"make": make}
    return words


WIKIPEDIA_WORDS = get_words('fixtures/makes_models_from_wikipedia.csv')

SHORT_WORDS = get_words('fixtures/makes_models_short.csv')

SHORT_WORDS_IMMUTABLE_INFO = {key: Info(**value) for key, value in SHORT_WORDS.items()}


with open(os.path.join(current_dir, 'fixtures/synonyms.json'), 'r') as the_file:
    SYNONYMS = json.loads(the_file.read())


class TestAutocomplete:

    @pytest.mark.parametrize("word, max_cost, size, expected_results", [
        ('bmw', 2, 3, {0: [['bmw']], 1: [['bmw e9'], ['bmw e3'], ['bmw m1'], ['bmw z1']]}),
        ('beemer', 2, 3, {}),
        ('honda covic', 2, 3, {0: [['honda']], 1: [['honda', 'civic'], ['honda', 'civic type r']]}),
    ])
    def test_search_without_synonyms(self, word, max_cost, size, expected_results):
        auto_complete = AutoComplete(words=WIKIPEDIA_WORDS)
        results, find_steps = auto_complete._find(word, max_cost, size)
        results = dict(results)
        print_results(locals())
        assert expected_results == results


STEP_DESCENDANTS_ONLY = [FindStep.descendants_only]
STEP_FUZZY_FOUND = [FindStep.fuzzy_try, FindStep.fuzzy_found]

SEARCH_CASES = [
    {'word': ' ',
     'max_cost': 3,
     'size': 3,
     'expected_find_results': {1: [['a'], ['c'], ['e'], ['m']]},
     'expected_steps': STEP_DESCENDANTS_ONLY,
     'expected_find_and_sort_results': [['a'], ['c'], ['e']],
     },
    {'word': '',
     'max_cost': 3,
     'size': 3,
     'expected_find_results': {1: [['a'], ['c'], ['e'], ['m']]},
     'expected_steps': STEP_DESCENDANTS_ONLY,
     'expected_find_and_sort_results': [['a'], ['c'], ['e']],
     },
    {'word': 'c',
     'max_cost': 3,
     'size': 3,
     'expected_find_results': {0: [['c']], 1: [['ct'], ['cl'], ['clk'], ['clc']]},
     'expected_steps': STEP_DESCENDANTS_ONLY,
     'expected_find_and_sort_results': [['c'], ['ct'], ['cl']],
     },
    {'word': 'ca',
     'max_cost': 3,
     'size': 3,
     'expected_find_results': {1: [['camry'], ['caddy'], ['cabriolet'], ['california']]},
     'expected_steps': STEP_DESCENDANTS_ONLY,
     'expected_find_and_sort_results': [['camry'], ['caddy'], ['cabriolet']],
     },
    {'word': 'camr',
     'max_cost': 3,
     'size': 6,
     'expected_find_results': {1: [['camry']]},
     'expected_steps': STEP_DESCENDANTS_ONLY,
     'expected_find_and_sort_results': [['camry']],
     },
    {'word': '4d',
     'max_cost': 3,
     'size': 3,
     'expected_find_results': {1: [['4c'], ['4runner']]},
     'expected_steps': STEP_DESCENDANTS_ONLY,
     'expected_find_and_sort_results': [['4c'], ['4runner']],
     },
    {'word': '2018 alpha ',
     'max_cost': 3,
     'size': 3,
     'expected_find_results': {0: [['2018']],
                               2: [['2018', 'alfa romeo'],
                                   ['2018', 'alfa romeo 4c'],
                                   ['2018', 'alfa romeo 6c'],
                                   ['2018', 'alfa romeo 8c'],
                                   ['2018', 'alfa romeo 33']]},
     'expected_steps': STEP_FUZZY_FOUND,
     'expected_find_and_sort_results': [['2018'], ['2018', 'alfa romeo'], ['2018', 'alfa romeo 4c']],
     },
    {'word': '2018 alpha romeo 4d',
     'max_cost': 3,
     'size': 4,
     'expected_find_results': {0: [['2018']],
                               1: [['2018', 'alfa romeo'],
                                   ['2018', 'alfa romeo rl'],
                                   ['2018', 'alfa romeo rm'],
                                   ['2018', 'alfa romeo 4c'],
                                   ['2018', 'alfa romeo 6c']],
                               2: [['2018', 'alfa romeo', 'ameo']]},
     'expected_steps': [FindStep.fuzzy_try, FindStep.fuzzy_found, {FindStep.rest_of_fuzzy_round2: [FindStep.fuzzy_try, FindStep.fuzzy_found]}, FindStep.not_enough_results_add_some_descandants],
     'expected_find_and_sort_results': [['2018'],
                                        ['2018', 'alfa romeo'],
                                        ['2018', 'alfa romeo rl'],
                                        ['2018', 'alfa romeo rm']],
     },
    {'word': '2018 alpha',
     'max_cost': 3,
     'size': 3,
     'expected_find_results': {0: [['2018']],
                               2: [['2018', 'alfa romeo'],
                                   ['2018', 'alfa romeo 4c'],
                                   ['2018', 'alfa romeo 6c'],
                                   ['2018', 'alfa romeo 8c'],
                                   ['2018', 'alfa romeo 33']]},
     'expected_steps': STEP_FUZZY_FOUND,
     'expected_find_and_sort_results': [['2018'], ['2018', 'alfa romeo'], ['2018', 'alfa romeo 4c']],
     },
    {'word': '2018 alfa',
     'max_cost': 3,
     'size': 3,
     'expected_find_results': {0: [['2018', 'alfa romeo']],
                               1: [['2018', 'alfa romeo rl'],
                                   ['2018', 'alfa romeo rm'],
                                   ['2018', 'alfa romeo 4c'],
                                   ['2018', 'alfa romeo 6c']]},
     'expected_steps': STEP_DESCENDANTS_ONLY,
     'expected_find_and_sort_results': [['2018', 'alfa romeo'], ['2018', 'alfa romeo rl'], ['2018', 'alfa romeo rm']],
     },
    {'word': '2018 alfg',
     'max_cost': 3,
     'size': 3,
     'expected_find_results': {0: [['2018']],
                               1: [['2018', 'alfa romeo'],
                                   ['2018', 'alfa romeo rl'],
                                   ['2018', 'alfa romeo rm'],
                                   ['2018', 'alfa romeo 4c']]},
     'expected_steps': STEP_DESCENDANTS_ONLY,
     'expected_find_and_sort_results': [['2018'], ['2018', 'alfa romeo'], ['2018', 'alfa romeo rl']],
     },
    {'word': '2018 glfa',
     'max_cost': 3,
     'size': 3,
     'expected_find_results': {0: [['2018']], 1: [['2018', 'gla']]},
     'expected_steps': STEP_DESCENDANTS_ONLY,
     'expected_find_and_sort_results': [['2018'], ['2018', 'gla']],
     },
    {'word': '2018 doyota',
     'max_cost': 3,
     'size': 3,
     'expected_find_results': {0: [['2018']],
                               1: [['2018', 'toyota'],
                                   ['2018', 'toyota 86'],
                                   ['2018', 'toyota aygo'],
                                   ['2018', 'toyota vios'],
                                   ['2018', 'toyota noah']]},
     'expected_steps': STEP_FUZZY_FOUND,
     'expected_find_and_sort_results': [['2018'], ['2018', 'toyota'], ['2018', 'toyota 86']],
     },
    {'word': '2018 doyota camr',
     'max_cost': 3,
     'size': 3,
     'expected_find_results': {0: [['2018']],
                               1: [['2018', 'toyota', 'camry'],
                                   ['2018', 'dyna'],
                                   ['2018', 'drifter'],
                                   ['2018', 'dauphine']]},
     'expected_steps': [FindStep.fuzzy_try, FindStep.fuzzy_found, {FindStep.rest_of_fuzzy_round2: [FindStep.descendants_only]}, FindStep.not_enough_results_add_some_descandants],
     'expected_find_and_sort_results': [['2018'], ['2018', 'toyota', 'camry'], ['2018', 'dyna']],
     },
    {'word': '2018 beemer',
     'max_cost': 3,
     'size': 3,
     'expected_find_results': {0: [['2018', 'bmw']],
                               1: [['2018', 'bmw e9'],
                                   ['2018', 'bmw e3'],
                                   ['2018', 'bmw m1'],
                                   ['2018', 'bmw z1']]},
     'expected_steps': STEP_DESCENDANTS_ONLY,
     'expected_find_and_sort_results': [['2018', 'bmw'], ['2018', 'bmw e9'], ['2018', 'bmw e3']],
     },
    {'word': '2018 beener',
     'max_cost': 3,
     'size': 3,
     'expected_find_results': {0: [['2018']],
                               1: [['2018', 'bmw'],
                                   ['2018', 'beetle'],
                                   ['2018', 'bmw e9'],
                                   ['2018', 'bmw e3']]},
     'expected_steps': [FindStep.fuzzy_try, FindStep.not_enough_results_add_some_descandants],
     'expected_find_and_sort_results': [['2018'], ['2018', 'bmw'], ['2018', 'beetle']],
     },
    {'word': 'vw bea',
     'max_cost': 3,
     'size': 3,
     'expected_find_results': {0: [['volkswagen']], 1: [['volkswagen beetle']]},
     'expected_steps': STEP_DESCENDANTS_ONLY,
     'expected_find_and_sort_results': [['volkswagen'], ['volkswagen beetle']],
     },
    {'word': 'toyota camry 2018',
     'max_cost': 3,
     'size': 5,
     'expected_find_results': {0: [['toyota', 'toyota camry', '2018']]},
     'expected_steps': STEP_DESCENDANTS_ONLY,
     'expected_find_and_sort_results': [['toyota', 'toyota camry', '2018']],
     },
    {'word': 'type r',
     'max_cost': 3,
     'size': 5,
     'expected_find_results': {0: [['type', 'type r']]},
     'expected_steps': STEP_DESCENDANTS_ONLY,
     'expected_find_and_sort_results': [['type', 'type r']],
     },
]


SEARCH_CASES_PARAMS = parameterize_cases(SEARCH_CASES)


class TestAutocompleteWithSynonyms:

    @pytest.mark.parametrize("word, max_cost, size, expected_find_results, expected_steps, expected_find_and_sort_results", SEARCH_CASES_PARAMS)
    def test_find(self, word, max_cost, size, expected_find_results, expected_steps, expected_find_and_sort_results):
        expected_results = expected_find_results
        auto_complete = AutoComplete(words=WIKIPEDIA_WORDS, synonyms=SYNONYMS)
        results, find_steps = auto_complete._find(word, max_cost, size)
        results = dict(results)
        print_results(locals())
        assert expected_results == results
        assert expected_steps == find_steps

    @pytest.mark.parametrize("word, max_cost, size, expected_find_results, expected_steps, expected_find_and_sort_results", SEARCH_CASES_PARAMS)
    def test__find_and_sort(self, word, max_cost, size, expected_find_results, expected_steps, expected_find_and_sort_results):
        expected_results = expected_find_and_sort_results
        auto_complete = AutoComplete(words=WIKIPEDIA_WORDS, synonyms=SYNONYMS)
        results = auto_complete._find_and_sort(word, max_cost, size)
        results = list(results)
        search_results = auto_complete.search(word, max_cost, size)
        print_results(locals())
        assert expected_results == results
        if word.strip():
            assert expected_results == search_results
        else:
            assert [] == search_results

    @pytest.mark.parametrize("word", [
        'alf',
    ])
    def test_immutable_info(self, word):
        auto_complete = AutoComplete(words=SHORT_WORDS, synonyms=SYNONYMS)
        auto_complete_immutable = AutoComplete(words=SHORT_WORDS_IMMUTABLE_INFO, synonyms=SYNONYMS)
        search_results = auto_complete._find(word, max_cost=3, size=3)
        search_results_immutable = auto_complete_immutable._find(word, max_cost=3, size=3)
        print_results(locals())
        assert search_results_immutable == search_results


class AutoCompleteWithSynonymsShort(DrawGraphMixin, AutoComplete):
    pass


class AutoCompleteWithSynonymsShortWithAnim(AutoCompleteWithSynonymsShort):

    DRAW_POPULATION_ANIMATION = True
    DRAW_POPULATION_ANIMATION_PATH = os.path.join(current_dir, 'animation/short_.svg')
    DRAW_POPULATION_ANIMATION_FILENO_PADDING = 6


class TestAutoCompleteWithSynonymsShortGraphDraw:

    def test_draw_graph(self):
        auto_complete = AutoCompleteWithSynonymsShort(words=SHORT_WORDS)
        file_path = os.path.join(current_dir, 'AutoCompleteWithSynonymsShort_Graph.svg')
        auto_complete.draw_graph(file_path)

    def test_draw_graph_animation(self):
        AutoCompleteWithSynonymsShortWithAnim(words=SHORT_WORDS)


class TestPrefixAndDescendants:

    @pytest.mark.parametrize("word, expected_matched_prefix_of_last_word, expected_rest_of_word, expected_matched_words, expected_node_path", [
        ('2018 alpha blah blah', 'al', 'pha blah blah', ['2018'], 'a,l'),
        ('2018 alpha ', 'al', 'pha ', ['2018'], 'a,l'),
        ('2018 alfa', '', '', ['2018', 'alfa romeo'], 'a,l,f,a'),
        ('2018 alf', 'alf', '', ['2018'], 'a,l,f'),
        ('2018 alfa romeo', '', '', ['2018', 'alfa romeo'], 'a,l,f,a, ,r,o,m,e,o'),
        ('1 series bmw 2007 2018', '', '', ['1 series', 'bmw', '2007', '2018'], '2,0,1,8'),
        ('200 chrysler', '', '', ['200', 'chrysler'], 'c,h,r,y,s,l,e,r'),
        ('200 chrysler 200', '', '', ['200', 'chrysler', 'chrysler 200'], 'c,h,r,y,s,l,e,r, ,2,0,0'),
        ('chrysler 2007', '', '', ['chrysler', '2007'], '2,0,0,7'),
        ('type r', '', '', ['type', 'type r'], 't,y,p,e, ,r'),
    ])
    def test_prefix_autofill(self, word, expected_matched_prefix_of_last_word,
                             expected_rest_of_word, expected_matched_words, expected_node_path):
        auto_complete = AutoComplete(words=WIKIPEDIA_WORDS, synonyms=SYNONYMS)
        matched_prefix_of_last_word, rest_of_word, node, matched_words = auto_complete._prefix_autofill(word)
        print(f'word: {word}')
        print(f'expected_matched_prefix_of_last_word: {expected_matched_prefix_of_last_word}')
        print(f'matched_prefix_of_last_word: {matched_prefix_of_last_word}')
        print(f'expected_rest_of_word: {expected_rest_of_word}')
        print(f'rest_of_word: {rest_of_word}')
        print(f'node: {node}')
        print(f'expected_matched_words: {expected_matched_words}')
        print(f'matched_words: {matched_words}')
        expected_node = auto_complete._dawg
        for k in expected_node_path.split(','):
            expected_node = expected_node[k]
        assert expected_node is node
        assert expected_matched_prefix_of_last_word == matched_prefix_of_last_word
        assert expected_rest_of_word == rest_of_word
        assert expected_matched_words == matched_words

    @pytest.mark.parametrize("word, expected_result", [
        ('2018 alpha ', ['alfa', 'alfa rl', 'alfa rm']),
        ('1 series bmw 2', ['bmw 2 series']),
        ('2018 alfa', ['alfa rl', 'alfa rm', 'alfa 4c']),
    ])
    def test_get_descendants_nodes(self, word, expected_result):
        auto_complete = AutoComplete(words=WIKIPEDIA_WORDS, synonyms=SYNONYMS)
        matched_prefix_of_last_word, rest_of_word, node, matched_words = auto_complete._prefix_autofill(word)
        found_words_gen = node.get_descendants_nodes(size=2)
        found_words = [_node.word for _node in found_words_gen]
        print(f'word: {word}')
        print(f'expected_result: {expected_result}')
        print(f'found_words: {found_words}')
        assert expected_result == list(found_words)
