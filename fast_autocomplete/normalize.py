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


def _remove_invalid_chars(x):
    result = x in valid_chars_for_node_name
    if x == '-' == _remove_invalid_chars.prev_x:
        result = False
    _remove_invalid_chars.prev_x = x
    return result


def remove_any_special_character(name):
    """
    Only remove invalid characters from a name. Useful for cleaning the user's original word.
    """
    name = name.lower()[:MAX_WORD_LENGTH]
    _remove_invalid_chars.prev_x = ''

    return ''.join(filter(_remove_invalid_chars, name)).strip()


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
