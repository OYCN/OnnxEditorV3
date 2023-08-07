#!/bin/bash

set -e

SCRIPT_DIR=$(
  cd "$(dirname "${0}")/../" || exit
  pwd
)

pushd "${SCRIPT_DIR}/onnxeditor/gui/res"
pyside6-rcc res.qrc -o res.p
popd

pushd "${SCRIPT_DIR}/onnxeditor/gui/ui/iosummary"
pyside6-uic iosummary.ui -o ui_iosummary.py
popd

pushd "${SCRIPT_DIR}/onnxeditor/gui/ui/nodesummary"
pyside6-uic nodesummary.ui -o ui_nodesummary.py
popd
