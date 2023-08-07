from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase
from .main_window import MainWindow
from .graph_editor import GraphEditor
from ..ir import Model


def entry(irm: Model | None = None, path: str | None = None):
    app = QApplication([])
    font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
    app.setFont(font)
    mw = MainWindow(irm, path)
    mw.show()
    app.exec()
