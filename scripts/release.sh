#!/bin/bash

set -e

SCRIPT_DIR=$(
  cd "$(dirname "${0}")/../" || exit
  pwd
)

pip install --user --upgrade setuptools wheel twine

rm ${SCRIPT_DIR}/dist/*

python setup.py check
python setup.py sdist bdist_wheel
twine upload dist/*
