import io
import os
import csv
import sys
import termios
import fcntl


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


def read_single_keypress():
    """Waits for a single keypress on stdin.
    https://stackoverflow.com/a/6599441/1497443

    This is a silly function to call if you need to do it a lot because it has
    to store stdin's current setup, setup stdin for reading single keystrokes
    then read the single keystroke then revert stdin back after reading the
    keystroke.

    Returns the character of the key that was pressed (zero on
    KeyboardInterrupt which can happen when a signal gets handled)

    """
    fd = sys.stdin.fileno()
    # save old state
    flags_save = fcntl.fcntl(fd, fcntl.F_GETFL)
    attrs_save = termios.tcgetattr(fd)
    # make raw - the way to do this comes from the termios(3) man page.
    attrs = list(attrs_save)  # copy the stored version to update
    # iflag
    attrs[0] &= ~(termios.IGNBRK | termios.BRKINT | termios.PARMRK |
                  termios.ISTRIP | termios.INLCR | termios.IGNCR |
                  termios.ICRNL | termios.IXON)
    # oflag
    attrs[1] &= ~termios.OPOST
    # cflag
    attrs[2] &= ~(termios.CSIZE | termios. PARENB)
    attrs[2] |= termios.CS8
    # lflag
    attrs[3] &= ~(termios.ECHONL | termios.ECHO | termios.ICANON |
                  termios.ISIG | termios.IEXTEN)
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    # turn off non-blocking
    fcntl.fcntl(fd, fcntl.F_SETFL, flags_save & ~os.O_NONBLOCK)
    # read a single keystroke
    try:
        ret = sys.stdin.read(1)  # returns a single character
    except KeyboardInterrupt:
        ret = 0
    finally:
        # restore old state
        termios.tcsetattr(fd, termios.TCSAFLUSH, attrs_save)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags_save)
    return ret
