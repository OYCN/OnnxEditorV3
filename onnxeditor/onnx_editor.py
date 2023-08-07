import sys
from . import entry

def main():
  if len(sys.argv) == 1:
    entry()
  elif len(sys.argv) == 2:
    entry(path=sys.argv[1])