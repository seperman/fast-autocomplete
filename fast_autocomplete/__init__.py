# flake8: noqa
import sys
from importlib import metadata

if sys.version_info < (3, 8):
    sys.exit('fast-autocomplete requires Python 3.8 or later.')

try:
    __version__ = metadata.version("fast-autocomplete")
except metadata.PackageNotFoundError:
    __version__ = "unknown"

from fast_autocomplete.dwg import AutoComplete
from fast_autocomplete.draw import DrawGraphMixin
from fast_autocomplete.demo import demo
from fast_autocomplete.loader import autocomplete_factory
from fast_autocomplete.normalize import Normalizer
