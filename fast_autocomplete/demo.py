from pprint import pprint
from fast_autocomplete.misc import read_single_keypress


def demo(running_modules, max_cost, size):
    """
    Gets an Autocomplete instance that has already data in it and you can then run search on it in real time
    """

    word_list = []

    running_modules = running_modules if isinstance(running_modules, dict) else {running_modules.__class__.__name__: running_modules}

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
        results = {}
        for module_name, module in running_modules.items():
            results[module_name] = module.search(word=joined, max_cost=max_cost, size=size)
        pprint(results)
        print('')
