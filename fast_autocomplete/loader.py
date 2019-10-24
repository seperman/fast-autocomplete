import os
import gzip
import json
import logging
try:
    from redis import StrictRedis
except ImportError:
    StrictRedis = None

from typing import Any, Dict, List, NamedTuple, Optional, Set, Tuple, Union
from fast_autocomplete import AutoComplete


def read_local_dump(filepath: str):
    with open(filepath, 'r') as the_file:
        return the_file.read()


def _simple_compress(item: str, hash_to_val: Dict[int, str]) -> str:
    item_hash = hash(item)
    if item_hash in hash_to_val:
        item = hash_to_val[item_hash]
    else:
        hash_to_val[item_hash] = item
    return item


class WordValue(NamedTuple):
    context: Any
    display: Any
    count: int = 0
    original_key: 'WordValue' = None

    def get(self, key: str, default: Optional[str] = None) -> str:
        result = getattr(self, key)
        if result is None:
            result = default
        return result


def get_all_content(content_files, redis_client=None, redis_key_prefix=None, logger=None):
    """
    Get all content that is needed to initialize Autocomplete.

    :param: redis_client (optional) If passed, it tries to load from Redis if there is already cached data
    """
    kwargs = {}
    for key, info in content_files.items():
        kwargs[key] = get_data(
            filepath=info['filepath'],
            compress=info['compress'],
            redis_client=redis_client,
            redis_key_prefix=redis_key_prefix,
            logger=logger
        )
    if logger:
        kwargs['logger'] = logger
    return kwargs


def get_data(filepath: str, compress: bool = False,
             redis_client: Optional[StrictRedis] = None,
             redis_key_prefix: Optional[str] = None,
             logger: Optional[logging.RootLogger] = None) -> Dict[str, List[str]]:
    data_json = None
    filename = os.path.basename(filepath)
    if redis_client and redis_key_prefix:
        key = redis_key_prefix.format(filename)
        try:
            data_json = redis_client.get(key)
        except Exception:
            if logger:
                logger.exception('Unable to get the search graph words from Redis.')
            else:
                print('Unable to get the search graph words from Redis.')
        if data_json:
            data_json = gzip.decompress(data_json).decode('utf-8')
    if not data_json:
        data_json = read_local_dump(filepath)
    data = json.loads(data_json)

    if compress:
        hash_to_val = {}

        for word, value in data.items():
            context, display, count = value
            display = _simple_compress(item=display, hash_to_val=hash_to_val)
            for key, val in context.items():
                context[key] = _simple_compress(
                    item=context[key], hash_to_val=hash_to_val
                )
            data[word] = WordValue(context=context, display=display, count=count)

    return data


def populate_redis(content_files, redis_client, redis_cache_prefix):
    """
    Populate Redis with data based on the local files
    """
    for key, info in content_files.items():
        filename = os.path.basename(info['filepath'])
        redis_key = redis_cache_prefix.format(filename)
        data = read_local_dump(info['filepath'])
        compressed = gzip.compress(data.encode('utf-8'))
        redis_client.set(redis_key, compressed)


def autocomplete_factory(
    content_files, redis_client=None, module=AutoComplete, logger=None
):
    """
    Factory function to initialize the proper Vehicle Autocomplete object

    :param: content_files: The file paths and options where data is stored.

    Example

        content_files = {
            'synonyms': {
                'filename': 'path/to/synonyms.json',
                'compress': False
            },
            'words': {
                'filename': 'path/to/words.json',
                'compress': True
            },
            'full_stop_words': {
                'filename': 'path/to/full_stop_words.json',
                'compress': False
            }
        }

    :param: redis_client: (optional) If passed, the factor function tries to load the data from Redis
                                     and if that fails, it will load the local data.
    :param: module: (optional) The AutoComplete module to initialize
    """
    kwargs = get_all_content(content_files, redis_client=redis_client, logger=logger)
    return module(**kwargs)
