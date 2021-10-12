# flake8: noqa
import sys
import pkg_resources

if (sys.version_info[0], sys.version_info[1]) < (3, 6):
    sys.exit('fast-autocomplete requires Python 3.6 or later.')

__version__ = pkg_resources.get_distribution("fast-autocomplete").version

from fast_autocomplete.dwg import AutoComplete
from fast_autocomplete.draw import DrawGraphMixin
from fast_autocomplete.demo import demo
from fast_autocomplete.loader import autocomplete_factory
from fast_autocomplete.normalize import Normalizer
