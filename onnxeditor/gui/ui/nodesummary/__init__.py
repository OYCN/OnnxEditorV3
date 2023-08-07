import os
# import sys

try:
    from .ui_nodesummary import Ui_NodeSummary
except ImportError:
    dir = os.path.dirname(__file__)
    # sys.path.append(dir)
    target = os.path.join(dir, 'ui_nodesummary.py')
    if not os.path.exists(target):
        os.system(
            f'cd {dir} && pyside6-uic nodesummary.ui -o ui_nodesummary.py')

from .ui_nodesummary import Ui_NodeSummary
from .nodesummary import NodeSummary
