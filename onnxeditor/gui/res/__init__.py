import os
# import sys

try:
    from .res import *
except ImportError:
    dir = os.path.dirname(__file__)
    # sys.path.append(dir)
    target = os.path.join(dir, 'res.py')
    if not os.path.exists(target):
        os.system(f'cd {dir} && pyside6-rcc res.qrc -o res.py')

from .res import *
