# flake8: noqa
import sys
import pkg_resources

pyversion = float(sys.version[:3])
if pyversion < 3.6:
    sys.exit('fast-autocomplete requires Python 3.6 or later.')

__version__ = pkg_resources.get_distribution("fast-autocomplete").version

from fast_autocomplete.dwg import AutoComplete
from fast_autocomplete.draw import DrawGraphMixin
from fast_autocomplete.demo import demo
from fast_autocomplete.normalize import normalize_node_name, remove_any_special_character
