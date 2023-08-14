from typing import Optional, Union
import PySide6.QtCore
from PySide6.QtWidgets import QDialog, QWidget, QDialogButtonBox, QFileDialog, QMessageBox
from PySide6.QtCore import Qt, Slot, Signal
from ....ir import Variable, TensorType
from .ui_datainspector import Ui_DataInspector
import re
import os
import numpy as np


class DataInspector(QDialog):
    def __init__(self, vir: Union[Variable, None] = None, parent: Union[QWidget, None] = None, display_name: bool = True) -> None:
        super().__init__(parent)
        self._ui = Ui_DataInspector()
        self._ui.setupUi(self)
        
        if not display_name:
            self._ui.name_label.hide()
            self._ui.var_name.hide()

        self.handle_map = {
            'npy': (' single tensor', self.handle_npy),
        }

        self._ui.file_btn.clicked.connect(self.file_brow)
        self._ui.load_btn.clicked.connect(self.load_file)
        self._ui.dump_to_btn.clicked.connect(self.dump_file)

        self._data: Union[np.ndarray, None] = None
        
        if vir is not None:
            self._ui.var_name.setText(vir.name)
            self._data = vir.data.getNp()
        
        self.flush_data_info()

    def flush_data_info(self):
        b = self._ui.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        if self._data is None:
            s = f'No Data Loaded'
            self._ui.dump_to_btn.setDisabled(True)
            b.setDisabled(True)
        else:
            s = f'Type: {self._data.dtype}\nShape: {list(self._data.shape)}'
            self._ui.dump_to_btn.setDisabled(False)
            b.setDisabled(False)
        self._ui.data_info.setText(s)
        
    def file_brow(self):
        path = QFileDialog.getOpenFileName(self, "open data file", "/", ' '.join([f'*.{k}' for k in self.handle_map]))
        if path is None or len(path[0]) == 0:
            return
        else:
            self._ui.path_edit.setText(path)
    
    @Slot()
    def dump_file(self):
        path = QFileDialog.getSaveFileName(self, "save data file", self._path, '*.npy')
        if path is None or len(path[0]) == 0:
            return
        else:
            try:
                np.save(path, self._data)
            except Exception as e:
                QMessageBox.warning(self, "dump error", str(e))
    
    @Slot()
    def load_file(self):
        path = self._ui.path_edit.text()
        suffix = path.split('.')[-1]
        print(suffix)
        if suffix not in self.handle_map:
            t = ',\n'.join([f'*.{k}' for k in self.handle_map])
            QMessageBox.warning(self, "suffix not support", f'we not support this suffix, we only support:\n[\n{t}\n]')
            self._data = None
        else:
            try:
                self._data = self.handle_map[suffix][1](path)
            except Exception as e:
                QMessageBox.warning(self, "data file load error", str(e))
                self._data = None
        self.flush_data_info()

    def handle_npy(self, path):
        self._data = np.load(path)
        
    def getRet(self):
        return self._data, self._ui.var_name.text()
