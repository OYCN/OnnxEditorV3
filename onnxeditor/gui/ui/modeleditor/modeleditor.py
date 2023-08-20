from typing import Optional, Any, Union
import PySide6.QtCore
from PySide6.QtWidgets import QDialog, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QTextEdit
from PySide6.QtCore import Qt, Slot, Signal
from ....ir import Model
import re
import numpy as np
import json


class ModelEditor(QDialog):
    def __init__(self, irm: Model, parent: Union[QWidget, None] = None) -> None:
        super().__init__(parent)

        vl = QVBoxLayout()

        self._key = {'ir_version': (QLineEdit(), int, 0), 'producer_name': (QLineEdit(), str, ''), 'producer_version': (QLineEdit(), str, ''),
                     'domain': (QLineEdit(), str, ''), 'model_version': (QLineEdit(), int, 0), 'doc_string': (QLineEdit(), str, 0)}
        for k, v in self._key.items():
            hl = QVBoxLayout()
            hl.addWidget(QLabel(f'{k}:'))
            t = getattr(irm, k)
            if not isinstance(t, v[1]):
                t = v[1](v[2])
            v[0].setText(str(t))
            hl.addWidget(v[0])
            vl.addLayout(hl)

        hl = QVBoxLayout()
        hl.addWidget(QLabel('opset_import:'))
        self._opset_import = QTextEdit()
        self._opset_import.setText(json.dumps(irm.opset_import, indent=2))
        hl.addWidget(self._opset_import)
        vl.addLayout(hl)

        self.setLayout(vl)

    def getRet(self):
        ret = {k: v[1](v[0].text()) for k, v in self._key.items()}
        ret['opset_import'] = json.loads(self._opset_import.toPlainText())
        return ret
