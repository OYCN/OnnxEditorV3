from typing import Optional, Union
import PySide6.QtCore
from PySide6.QtWidgets import QDialog, QWidget, QDialogButtonBox
from PySide6.QtCore import Qt, Slot, Signal
from ....ir import Variable, TensorType
from .ui_iosummary import Ui_IOSummary
import re


class IOSummary(QDialog):
    def __init__(self, vir: Variable | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._ui = Ui_IOSummary()
        self._ui.setupUi(self)

        self._ui.type_edit.addItems([e.value for e in TensorType])

        if vir is not None:
            self._ui.name_edit.setText(vir.name)
            self._ui.name_edit.setDisabled(True)
            self._ui.dim_edit.setText(','.join([str(v) for v in vir.shape]))
            idx = self._ui.type_edit.findText(vir.type.value)
            self._ui.type_edit.setCurrentIndex(idx)
        self._ui.dim_edit.textChanged.connect(self.dimCheckSlot)
        self.dimCheckSlot()

    def checkDim(self):
        txt = self._ui.dim_edit.text()
        return re.fullmatch(r'^((-?[0-9a-zA-Z]+),?)*$', txt) is not None
    
    def parseDim(self):
        txt = self._ui.dim_edit.text()
        assert self.checkDim()
        ret = re.findall(r'(-?[0-9a-zA-Z]+)', txt)
        return list(ret)

    
    def getRet(self):
        return {
            'name': self._ui.name_edit.text(),
            'shape': self.parseDim(),
            'type': TensorType(self._ui.type_edit.currentText()),
        }

    @Slot()
    def dimCheckSlot(self):
        b = self._ui.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        b.setEnabled(self.checkDim())
