from pprint import pprint
from fast_autocomplete.misc import read_single_keypress


def demo(autocomplete, max_cost, size):
    """
    Gets an Autocomplete instance that has already data in it and you can then run search on it in real time
    """

    word_list = []

    print('FAST AUTOCOMPLETE DEMO')
    print('Press any key to search for. Press ctrl+c to exit')

    while True:
        pressed = read_single_keypress()
        if pressed == '\x7f':
            if word_list:
                word_list.pop()
        elif pressed == '\x03':
            break
        else:
            word_list.append(pressed)

        joined = ''.join(word_list)
        print(chr(27) + "[2J")
        print(joined)
        results = autocomplete.search(word=joined, max_cost=max_cost, size=size)
        pprint(results)
        print('')
