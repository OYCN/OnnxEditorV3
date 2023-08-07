import os
# import sys

try:
    from .ui_iosummary import Ui_IOSummary
except ImportError:
    dir = os.path.dirname(__file__)
    # sys.path.append(dir)
    target = os.path.join(dir, 'ui_iosummary.py')
    if not os.path.exists(target):
        os.system(
            f'cd {dir} && pyside6-uic iosummary.ui -o ui_iosummary.py')

from .ui_iosummary import Ui_IOSummary
from .iosummary import IOSummary
