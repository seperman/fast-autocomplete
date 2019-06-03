import os
import sys

current_file = os.path.dirname(__file__)
path1 = os.path.abspath(os.path.join(current_file, '..'))
path2 = os.path.abspath(os.path.join(current_file, 'tests'))
sys.path.append(path1) # noqa
sys.path.append(path2) # noqa
