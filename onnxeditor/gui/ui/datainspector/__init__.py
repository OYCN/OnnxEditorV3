import os
# import sys

try:
    from .ui_datainspector import Ui_DataInspector
except ImportError:
    dir = os.path.dirname(__file__)
    # sys.path.append(dir)
    target = os.path.join(dir, 'ui_datainspector.py')
    if not os.path.exists(target):
        os.system(
            f'cd {dir} && pyside6-uic datainspector.ui -o ui_datainspector.py')

from .ui_datainspector import Ui_DataInspector
from .datainspector import DataInspector
