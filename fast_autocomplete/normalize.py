import string
from fast_autocomplete.lfucache import LFUCache

valid_chars_for_string = {i for i in string.ascii_letters.lower()}
valid_chars_for_integer = {i for i in string.digits}
valid_chars_for_node_name = {' ', '-'} | valid_chars_for_string | valid_chars_for_integer

NORMALIZED_CACHE_SIZE = 2048
MAX_WORD_LENGTH = 40

_normalized_lfu_cache = LFUCache(NORMALIZED_CACHE_SIZE)


def normalize_node_name(name):
    name = name[:MAX_WORD_LENGTH]
    result = _normalized_lfu_cache.get(name)
    if result == -1:
        result = _get_normalized_node_name(name)
        _normalized_lfu_cache.set(name, result)
    return result


def _get_normalized_node_name(name):
    name = name.lower()
    result = []
    last_i = None
    for i in name:
        if i in valid_chars_for_node_name:
            if i == '-':
                i = ' '
            elif (i in valid_chars_for_integer and last_i in valid_chars_for_string) or (i in valid_chars_for_string and last_i in valid_chars_for_integer):
                result.append(' ')
            if not(i == last_i == ' '):
                result.append(i)
                last_i = i
    return ''.join(result).strip()
