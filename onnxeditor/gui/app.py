from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase
from .main_window import MainWindow
from ..ir import OnnxModel, OnnxImport
from typing import Union


def entry(model: Union[str, None]):
    app = QApplication([])
    font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
    app.setFont(font)
    mw = MainWindow()
    mw.open_file(model)
    mw.show()
    app.exec()
