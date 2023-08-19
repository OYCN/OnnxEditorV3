import os
# import sys

try:
    from .ui_findbar import Ui_FindBar
except ImportError:
    dir = os.path.dirname(__file__)
    # sys.path.append(dir)
    target = os.path.join(dir, 'ui_findbar.py')
    if not os.path.exists(target):
        os.system(
            f'cd {dir} && pyside6-uic findbar.ui -o ui_findbar.py')

from .ui_findbar import Ui_FindBar
from .findbar import FindBar
