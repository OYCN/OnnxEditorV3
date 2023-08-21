from PySide6.QtWidgets import QMainWindow, QTabWidget, QMenu, QFileDialog, QMessageBox
from PySide6.QtGui import QIcon, QAction, QKeySequence
from PySide6.QtCore import Slot, Qt
from .graph_editor import GraphEditor
from ..ir import Model, OnnxImport, OnnxExport, pass_const_to_var
from .ui import ModelEditor
import os
import onnx
import onnx.checker
from typing import Union


class MainWindow(QMainWindow):
    def __init__(self, irm: Union[Model, None] = None, path: Union[str, None] = None, parent=None):
        super().__init__(parent)
        self._imp = OnnxImport(pass_const_to_var)
        self._exp = OnnxExport()

        self.setWindowIcon(QIcon(":/img/appicon.ico"))
        self.resize(800, 600)
        # we will connect some signal to loaded ge
        self._lk2ge = []
        self.initActions()

        self._path = ''
        self._irm: Union[Model, None] = None
        self._ge: Union[GraphEditor, None] = None
        self.openFile(irm, path)

    def initActions(self):
        def addMenu(name: str, menu: QMenu = None):
            if menu is None:
                return self.menuBar().addMenu(name)
            else:
                return menu.addMenu(name)

        def addAction(menu: QMenu, name: str, fn=None):
            act = QAction(self)
            act.setText(name)
            if fn is not None:
                act.triggered.connect(fn)
            menu.addAction(act)
            return act
        # File
        menu = addMenu('File')
        act = addAction(menu, "Open File", self.fileOpenSlot)
        act.setStatusTip("Open an exist onnx file")
        act.setShortcut(QKeySequence('Ctrl+o'))
        act = addAction(menu, "Save", self.fileSaveSlot)
        act.setStatusTip("Save this onnx file")
        act.setShortcut(QKeySequence('Ctrl+s'))
        act = addAction(menu, "Save as", self.fileSaveAsSlot)
        act.setStatusTip("Save this onnx file as new file")
        act.setShortcut(QKeySequence('Ctrl+e'))
        # Edit
        menu = addMenu('Edit')
        act = addAction(menu, "Find")
        self._lk2ge.append(
            lambda ge, act=act: act.triggered.connect(ge.displayFindBar))
        act.setStatusTip("Display Find Bar")
        act.setShortcut(QKeySequence('Ctrl+f'))
        act = addAction(menu, "Model Properties", self.showModelEditDialog)
        act.setStatusTip("Edit model properties")

    def openFile(self, irm: Union[Model, None], path: Union[str, None]):
        if path is None:
            path = ''
            self._path = path
        elif irm is None:
            m = onnx.load(path)
            try:
                onnx.checker.check_model(m)
            except Exception as e:
                msb = QMessageBox(QMessageBox.Icon.Warning,
                                  "onnx checker error", str(e), parent=self)
                msb.setWindowModality(Qt.WindowModality.WindowModal)
                msb.show()
            irm = self._imp(path)
        if not path.startswith('(') and len(path) > 0:
            path = '(' + path + ')'
        self.setWindowTitle('OnnxEditor' + path)
        if irm is None:
            irm = Model()
        self._irm = irm
        self._ge = GraphEditor(irm.graph)
        self.setCentralWidget(self._ge)
        for fn in self._lk2ge:
            fn(self._ge)

    @Slot()
    def fileOpenSlot(self):
        path = QFileDialog.getOpenFileName(
            self, "open onnx file", "/", '*.onnx')
        if path is None or len(path[0]) == 0:
            return
        else:
            self.openFile(None, path[0])

    @Slot()
    def fileSaveSlot(self):
        if len(self._path) == 0:
            self.fileSaveAsSlot()
        else:
            m = self._exp(self._irm, self._path)
            try:
                onnx.checker.check_model(m)
            except Exception as e:
                QMessageBox.warning(self, "onnx checker error", str(e))

    @Slot()
    def fileSaveAsSlot(self):
        if len(self._path) == 0:
            self._path = "/"
        else:
            self._path = os.path.dirname(self._path)
        path = QFileDialog.getSaveFileName(
            self, "save onnx file", self._path, '*.onnx')
        if path is None or len(path[0]) == 0:
            return
        else:
            m = self._exp(self._irm, path[0])
            try:
                onnx.checker.check_model(m)
            except Exception as e:
                QMessageBox.warning(self, "onnx checker error", str(e))

    @Slot()
    def showModelEditDialog(self):
        dialog = ModelEditor(self._irm, self)
        dialog.exec()
        ret = dialog.getRet()
        for k, v in ret.items():
            setattr(self._irm, k, v)
