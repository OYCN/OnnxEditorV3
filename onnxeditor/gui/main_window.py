from PySide6.QtWidgets import QMainWindow, QTabWidget, QMenu, QFileDialog, QMessageBox
from PySide6.QtGui import QIcon, QAction, QKeySequence
from PySide6.QtCore import Slot, Qt
from .editor import Editor
from ..ir import OnnxImport, OnnxExport, OnnxModel
from .ui import ModelEditor
import os
import onnx
import onnx.checker
from typing import Union


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowIcon(QIcon(":/img/appicon.ico"))
        self.resize(800, 600)
        self.__init_actions()

        self.__set_editor(Editor(OnnxModel(), self))

        self.__path = None

        self.__update_title()

    def __init_actions(self):
        def add_menu(name: str, menu: QMenu = None):
            if menu is None:
                return self.menuBar().addMenu(name)
            else:
                return menu.addMenu(name)

        def add_action(menu: QMenu, name: str, fn=None):
            act = QAction(self)
            act.setText(name)
            if fn is not None:
                act.triggered.connect(fn)
            menu.addAction(act)
            return act

        # File
        menu = add_menu("File")
        act = add_action(menu, "Open File", self.fileOpenSlot)
        act.setStatusTip("Open an exist onnx file")
        act.setShortcut(QKeySequence("Ctrl+o"))
        act = add_action(menu, "Save", self.fileSaveSlot)
        act.setStatusTip("Save this onnx file")
        act.setShortcut(QKeySequence("Ctrl+s"))
        act = add_action(menu, "Save as", self.fileSaveAsSlot)
        act.setStatusTip("Save this onnx file as new file")
        act.setShortcut(QKeySequence("Ctrl+e"))
        # Edit
        menu = add_menu("Edit")
        act = add_action(menu, "Find")
        act.setStatusTip("Display Find Bar")
        act.setShortcut(QKeySequence("Ctrl+f"))
        act = add_action(menu, "Model Properties", self.showModelEditDialog)
        act.setStatusTip("Edit model properties")

    def __update_title(self):
        if self.__path is None:
            self.setWindowTitle("OnnxEditor")
        else:
            self.setWindowTitle(f"OnnxEditor ({self.__path})")

    def __set_editor(self, editor):
        self.__editor = editor
        self.setCentralWidget(self.__editor)

    def open_model(self, model: Union[OnnxModel, str, None]):
        if model is None:
            model = OnnxModel()
            self.__path = None
        elif isinstance(model, str):
            model = OnnxImport()(model)
        assert isinstance(model, OnnxModel), (type(model), model)
        self.__set_editor(Editor(model, self))
        self.__update_title()

    @Slot()
    def file_open_slot(self):
        path = QFileDialog.getOpenFileName(self, "open onnx file", "/", "*.onnx")
        if path is None or len(path[0]) == 0:
            return
        else:
            self.open_model(path[0])

    @Slot()
    def file_save_slot(self):
        if len(self._path) == 0:
            self.fileSaveAsSlot()
        else:
            OnnxExport()(self.__editor.get_model_ir(), self._path)

    @Slot()
    def file_save_as_slot(self):
        if len(self._path) == 0:
            dir = "/"
        else:
            dir = os.path.dirname(self.__path)
        path = QFileDialog.getSaveFileName(self, "save onnx file", dir, "*.onnx")
        if path is None or len(path[0]) == 0:
            return
        else:
            OnnxExport()(self.__editor.get_model_ir(), path[0])
