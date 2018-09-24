import io
import os
import csv


class FileNotFound(ValueError):
    pass


def _check_file_exists(path):
    if not os.path.exists(path):
        raise FileNotFound(f'{path} does not exist')


def read_csv_gen(path_or_stringio, csv_func=csv.reader, **kwargs):
    """
    Takes a path_or_stringio to a file or a StringIO object and creates a CSV generator
    """
    if isinstance(path_or_stringio, (str, bytes)):
        _check_file_exists(path_or_stringio)
        encoding = kwargs.pop('encoding', 'utf-8-sig')
        with open(path_or_stringio, 'r', encoding=encoding) as csvfile:
            for i in csv_func(csvfile, **kwargs):
                yield i
    elif isinstance(path_or_stringio, io.StringIO):
        for i in csv_func(path_or_stringio, **kwargs):
            yield i
    else:
        raise TypeError('Either a path to the file or StringIO object needs to be passed.')


def _extend_and_repeat(list1, list2):
    if not list1:
        return [[i] for i in list2]

    result = []
    for item in list2:
        if item not in list1:
            list1_copy = list1.copy()
            if item.startswith(list1_copy[-1]):
                list1_copy.pop()
            list1_copy.append(item)
            result.append(list1_copy)

    return result
