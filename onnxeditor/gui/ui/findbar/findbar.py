from typing import Optional, Union
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QWidget, QDialogButtonBox, QGraphicsItem, QListWidgetItem
from PySide6.QtCore import Qt, Slot, Signal, QObject
from ....ir import Graph, Node, Variable
from .ui_findbar import Ui_FindBar
import re


class FindBar(QDialog):
    centerOn = Signal(QGraphicsItem)

    def __init__(self, gir: Graph, parent: Union[QWidget, None] = None) -> None:
        super().__init__(parent)
        self._ui = Ui_FindBar()
        self._ui.setupUi(self)

        self._ir = gir

        self._ui.btn_find.clicked.connect(self.doFind)

        self._ui.filter_node.setChecked(True)
        self._ui.filter_io.setChecked(True)
        self._ui.filter_var.setChecked(True)

        self._ui.ret_list.itemDoubleClicked.connect(self.onItemDoubleClicked)

        self.setWindowTitle('Find')

    def addItem(self, name: str, node: QGraphicsItem):
        item = QListWidgetItem(name)
        assert node is not None
        ir = node.ir
        if isinstance(ir, Node):
            item.setIcon(QIcon(":/img/node.png"))
        elif isinstance(ir, Variable):
            if not ir.used:
                item.setIcon(QIcon(":/img/unused.png"))
            else:
                if ir.isInput:
                    item.setIcon(QIcon(":/img/input.png"))
                elif ir.isOutput:
                    item.setIcon(QIcon(":/img/output.png"))
                elif ir.isConstant:
                    item.setIcon(QIcon(":/img/tensor4.png"))
                else:
                    item.setIcon(QIcon(":/img/var.png"))
        item.setData(Qt.ItemDataRole.UserRole, node)
        self._ui.ret_list.addItem(item)

    def clearItem(self):
        self._ui.ret_list.clear()

    @Slot()
    def doFind(self):
        self.clearItem()

        name = self._ui.le_name.text()
        type = self._ui.find_mod.currentText()

        if type == 'Has':
            def fn(s):
                return name in s
        elif type == 'StartWith':
            def fn(s):
                return s.startswith(name)
        elif type == 'EndsWith':
            def fn(s):
                return s.endswith(name)
        elif type == 'Regex':
            def fn(s):
                return re.fullmatch(name, s) is not None
        else:
            raise RuntimeError(f'Unknown find type: {type}')

        if self._ui.filter_node.isChecked():
            for n in self._ir.nodes:
                if fn(n.name):
                    self.addItem(n.name, n.read_ext('bind_gnode'))
        if self._ui.filter_io.isChecked():
            for v in self._ir.input:
                if fn(v.name):
                    self.addItem(v.name, v.read_ext('bind_gnode_src'))
            for v in self._ir.output:
                if fn(v.name):
                    self.addItem(v.name, v.read_ext('bind_gnode_dst'))
        if self._ui.filter_var.isChecked():
            for v in self._ir.variables:
                if fn(v.name):
                    self.addItem(v.name, v.read_ext('bind_gedge'))

    @Slot(QListWidgetItem)
    def onItemDoubleClicked(self, item: QListWidgetItem):
        it = item.data(Qt.ItemDataRole.UserRole)
        if it is not None:
            self.centerOn.emit(it)
