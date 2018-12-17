import collections
from enum import Enum
from threading import Lock
from collections import defaultdict
from fast_autocomplete.lfucache import LFUCache
from fast_autocomplete.misc import _extend_and_repeat
from Levenshtein import distance as levenshtein_distance

DELIMITER = '__'
ORIGINAL_KEY = 'original_key'
INF = float('inf')


class FindStep(Enum):
    start = 0
    descendants_only = 1
    fuzzy_try = 2
    fuzzy_found = 3
    rest_of_fuzzy_round2 = 4
    not_enough_results_add_some_descandants = 5


class AutoComplete:

    CACHE_SIZE = 2048

    def __init__(self, words, synonyms=None):
        """
        Inistializes the Autocomplete module

        :param words: A dictionary of words mapped to their context
        :param synonyms: (optional) A dictionary of words to their synonyms.
                         The synonym words should only be here and not repeated in words parameter.
        """
        self._lock = Lock()
        self._dwg = None
        self._raw_synonyms = synonyms or {}
        self._lfu_cache = LFUCache(self.CACHE_SIZE)
        self._clean_synonyms, self._partial_synonyms = self._get_clean_and_partial_synonyms()
        self._reverse_synonyms = self._get_reverse_synonyms(self._clean_synonyms)
        self.words = words
        new_words = self._get_partial_synonyms_to_words()
        self.words.update(new_words)
        self._populate_dwg()

    def _get_clean_and_partial_synonyms(self):
        """
        Synonyms are words that should produce the same results.

        - For example `beemer` and `bmw` should both give you `bmw`.
        - `alfa` and `alfa romeo` should both give you `alfa romeo`

        The synonyms get divided into 2 groups:

        1. clean synonyms: The 2 words share little or no words. For example `beemer` vs. `bmw`.
        2. partial synonyms: One of the 2 words is a substring of the other one. For example `alfa` and `alfa romeo` or `gm` vs. `gmc`.

        """
        clean_synonyms = {}
        partial_synonyms = {}

        for key, synonyms in self._raw_synonyms.items():
            key = key.strip().lower()
            _clean = []
            _partial = []
            for syn in synonyms:
                syn = syn.strip().lower()
                if key.startswith(syn):
                    _partial.append(syn)
                else:
                    _clean.append(syn)
            if _clean:
                clean_synonyms[key] = _clean
            if _partial:
                partial_synonyms[key] = _partial

        return clean_synonyms, partial_synonyms

    def _get_reverse_synonyms(self, synonyms):
        result = {}
        if synonyms:
            for key, value in synonyms.items():
                for item in value:
                    result[item] = key
        return result

    def _get_partial_synonyms_to_words(self):
        new_words = {}
        for key, value in self.words.items():
            # data is mutable so we copy
            try:
                value = value.copy()
            # data must be named tuple
            except Exception:
                new_value = value._asdict()
                new_value[ORIGINAL_KEY] = key
                value = type(value)(**new_value)
            else:
                value[ORIGINAL_KEY] = key
            for syn_key, syns in self._partial_synonyms.items():
                if key.startswith(syn_key):
                    for syn in syns:
                        new_key = key.replace(syn_key, syn)
                        new_words[new_key] = value
        return new_words

    def _populate_dwg(self):
        if not self._dwg:
            with self._lock:
                if not self._dwg:
                    self._dwg = _DawgNode()
                    for word, value in self.words.items():
                        original_key = value.get(ORIGINAL_KEY)
                        word = word.strip().lower()
                        leaf_node = self.insert_word_branch(word, original_key=original_key)
                        if self._clean_synonyms:
                            synonyms = self._clean_synonyms.get(word)
                            if synonyms:
                                for synonym in synonyms:
                                    self.insert_word_branch(synonym, leaf_node=leaf_node, add_word=False)

    def insert_word_callback(self, word):
        """
        Once word is inserted, run this.
        """
        pass

    def insert_word_branch(self, word, leaf_node=None, add_word=True, original_key=None):
        """
        Inserts a word into the Dawg.

        :param word: The word to be inserted as a branch of dwg
        :param leaf_node: (optional) The leaf node for the node to merge into in the dwg.
        :param add_word: (Boolean, default: True) Add the word itself at the end of the branch.
                          Usually this is set to False if we are merging into a leaf node and do not
                          want to add the actual word there.
        :param original_key: If the word that is being added was originally another word.
                             For example with synonyms, you might be inserting the word `beemer` but the
                             original key is `bmw`. This parameter might be removed in the future.

        """
        if leaf_node:
            temp_leaf_node = self._dwg.insert(word[:-1], add_word=add_word, original_key=original_key)
            temp_leaf_node.children[word[-1]] = leaf_node
        else:
            leaf_node = self._dwg.insert(word, original_key=original_key)
        self.insert_word_callback(word)
        return leaf_node

    def _find_and_sort(self, word, max_cost, size):
        output_keys_set = set()
        results, find_steps = self._find(word, max_cost, size)
        results_keys = list(results.keys())
        results_keys.sort()
        for key in results_keys:
            for output_items in results[key]:
                for i, item in enumerate(output_items):
                    reversed_item = self._reverse_synonyms.get(item)
                    if reversed_item:
                        output_items[i] = reversed_item
                    elif item not in self.words:
                        output_items[i] = None
                output_items_str = DELIMITER.join(output_items)
                if output_items and output_items_str not in output_keys_set:
                    output_keys_set.add(output_items_str)
                    yield output_items
                    if len(output_keys_set) >= size:
                        return

    def search(self, word, max_cost=2, size=5):
        """
        parameters:
        - word: the word to return autocomplete results for
        - max_cost: Maximum Levenshtein edit distance to be considered when calculating results
        - size: The max number of results to return
        """
        word = word.lower().strip()
        if not word:
            return []
        key = f'{word}-{max_cost}-{size}'
        result = self._lfu_cache.get(key)
        if result == -1:
            result = list(self._find_and_sort(word, max_cost, size))
            self._lfu_cache.set(key, result)
        return result

    @staticmethod
    def _len_results(results):
        return sum(map(len, results.values()))

    @staticmethod
    def _is_enough_results(results, size):
        return AutoComplete._len_results(results) >= size

    def _find(self, word, max_cost, size, call_count=0):
        """
        The search function returns a list of all words that are less than the given
        maximum distance from the target word
        """

        results = defaultdict(list)
        fuzzy_matches = defaultdict(list)
        rest_of_results = {}
        fuzzy_matches_len = 0

        fuzzy_min_distance = min_distance = INF
        matched_prefix_of_last_word, rest_of_word, new_node, matched_words = self._prefix_autofill(word=word)

        last_word = matched_prefix_of_last_word + rest_of_word

        if matched_words:
            results[0] = [matched_words.copy()]
            min_distance = 0
        if len(rest_of_word) < 3:
            find_steps = [FindStep.descendants_only]
            self._add_descendants_words_to_results(node=new_node, size=size, matched_words=matched_words, results=results, distance=1)
        else:
            find_steps = [FindStep.fuzzy_try]
            word_chunks = collections.deque(filter(lambda x: x, last_word.split(' ')))
            new_word = word_chunks.popleft()

            while len(new_word) < 5 and word_chunks:
                new_word = f'{new_word} {word_chunks.popleft()}'
            fuzzy_rest_of_word = ' '.join(word_chunks)

            for _word in self.words:
                if abs(len(_word) - len(new_word)) > max_cost:
                    continue
                dist = levenshtein_distance(new_word, _word)
                if dist < max_cost:
                    fuzzy_matches_len += 1
                    _value = self.words[_word].get(ORIGINAL_KEY, _word)
                    fuzzy_matches[dist].append(_value)
                    fuzzy_min_distance = min(fuzzy_min_distance, dist)
                    if fuzzy_matches_len >= size or dist < 2:
                        break
            if fuzzy_matches_len:
                find_steps.append(FindStep.fuzzy_found)
                if fuzzy_rest_of_word:
                    call_count += 1
                    if call_count < 2:
                        rest_of_results, rest_find_steps = self._find(word=fuzzy_rest_of_word, max_cost=max_cost, size=size, call_count=call_count)
                        find_steps.append({FindStep.rest_of_fuzzy_round2: rest_find_steps})
                for _word in fuzzy_matches[fuzzy_min_distance]:
                    if rest_of_results:
                        rest_of_results_min_key = min(rest_of_results.keys())
                        for _rest_of_matched_word in rest_of_results[rest_of_results_min_key]:
                            results[fuzzy_min_distance].append(matched_words + [_word] + _rest_of_matched_word)
                    else:
                        results[fuzzy_min_distance].append(matched_words + [_word])
                        not_used_matched_prefix_of_last_word, not_used_rest_of_word, fuzzy_new_node, not_used_matched_words = self._prefix_autofill(word=_word)
                        self._add_descendants_words_to_results(node=fuzzy_new_node, size=size, matched_words=matched_words, results=results, distance=fuzzy_min_distance)

            if matched_words and not self._is_enough_results(results, size):
                find_steps.append(FindStep.not_enough_results_add_some_descandants)
                total_min_distance = min(min_distance, fuzzy_min_distance)
                self._add_descendants_words_to_results(node=new_node, size=size, matched_words=matched_words, results=results, distance=total_min_distance+1)

        return results, find_steps

    def _prefix_autofill(self, word, node=None):
        len_prev_rest_of_last_word = INF
        matched_words = []
        matched_words_set = set()

        def _add_words(words):
            is_added = False
            for word in words:
                if word not in matched_words_set:
                    matched_words.append(word)
                    matched_words_set.add(word)
                    is_added = True
            return is_added

        matched_prefix_of_last_word, rest_of_word, node, matched_words_part = self._prefix_autofill_part(word, node)
        _add_words(matched_words_part)
        result = (matched_prefix_of_last_word, rest_of_word, node, matched_words)
        len_rest_of_last_word = len(rest_of_word)

        while len_rest_of_last_word and len_rest_of_last_word < len_prev_rest_of_last_word:
            word = matched_prefix_of_last_word + rest_of_word
            word = word.strip()
            len_prev_rest_of_last_word = len_rest_of_last_word
            matched_prefix_of_last_word, rest_of_word, node, matched_words_part = self._prefix_autofill_part(word, node=self._dwg)
            is_added = _add_words(matched_words_part)
            if is_added is False:
                break
            len_rest_of_last_word = len(rest_of_word)
            result = (matched_prefix_of_last_word, rest_of_word, node, matched_words)

        return result

    def _prefix_autofill_part(self, word, node=None):
        node = node or self._dwg
        que = collections.deque(word)

        matched_prefix_of_last_word = ''
        matched_words = []

        while que:
            char = que.popleft()

            if node.children:
                if char not in node.children:
                    que.appendleft(char)
                    break
                node = node.children[char]
                if char != ' ' or matched_prefix_of_last_word:
                    matched_prefix_of_last_word += char
                if node.word:
                    if que:
                        next_char = que[0]
                        if next_char != ' ':
                            continue
                    matched_prefix_of_last_word = ''
                    matched_words.append(node.value)
            else:
                if char == ' ':
                    node = self._dwg
                else:
                    que.appendleft(char)
                    break

        if not que and node.word:
            matched_prefix_of_last_word = ''
            matched_words.append(node.value)

        rest_of_word = "".join(que)

        return matched_prefix_of_last_word, rest_of_word, node, matched_words

    def _add_descendants_words_to_results(self, node, size, matched_words, results, distance):
        descendant_words = list(node.get_descendants_words(size))
        extended = _extend_and_repeat(matched_words, descendant_words)
        if extended:
            results[distance].extend(extended)
        return distance

    def _node_word_info_matches_condition(self, node, condition):
        _word = node.word
        word_info = self.words.get(_word)
        if word_info:
            return condition(word_info)
        else:
            return False

    def get_all_descendent_words_for_condition(self, word, size, condition):
        new_tokens = []

        matched_prefix_of_last_word, rest_of_word, node, matched_words_part = self._prefix_autofill_part(word=word)
        if not rest_of_word and self._node_word_info_matches_condition(node, condition):
            found_nodes_gen = node.get_descendants_nodes(size)
            for node in found_nodes_gen:
                if self._node_word_info_matches_condition(node, condition):
                    new_tokens.append(node.word)
        return new_tokens


class _DawgNode:
    """
    The Dawg data structure keeps a set of words, organized with one node for
    each letter. Each node has a branch for each letter that may follow it in the
    set of words.
    """

    __slots__ = ("word", "original_key", "children")

    def __init__(self):
        self.word = None
        self.original_key = None
        self.children = {}

    def __getitem__(self, key):
        return self.children[key]

    def insert(self, word, add_word=True, original_key=None):
        node = self
        for letter in word:
            if letter not in node.children:
                node.children[letter] = _DawgNode()

            node = node.children[letter]

        if add_word:
            node.word = word
            node.original_key = original_key
        return node

    @property
    def value(self):
        return self.original_key or self.word

    def __repr__(self):
        return f'< children: {list(self.children.keys())}, word: {self.word} >'

    def get_descendants_nodes(self, size):

        que = collections.deque()
        unique_nodes = {self}
        found_words_set = set()

        for letter, child_node in self.children.items():
            if child_node not in unique_nodes:
                unique_nodes.add(child_node)
                que.append((letter, child_node))

        while que:
            letter, child_node = que.popleft()
            child_value = child_node.value
            if child_value:
                if child_value not in found_words_set:
                    found_words_set.add(child_value)
                    yield child_node
                    if len(found_words_set) > size:
                        break

            for letter, grand_child_node in child_node.children.items():
                if grand_child_node not in unique_nodes:
                    unique_nodes.add(grand_child_node)
                    que.append((letter, grand_child_node))

    def get_descendants_words(self, size):
        found_words_gen = self.get_descendants_nodes(size)
        return map(lambda x: x.value, found_words_gen)
