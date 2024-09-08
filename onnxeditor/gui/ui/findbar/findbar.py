from typing import Union
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QWidget, QGraphicsItem, QListWidgetItem
from PySide6.QtCore import Qt, Slot, Signal
from ....ir import OnnxGraph, OnnxNode, OnnxVar
from .ui_findbar import Ui_FindBar
import re


class FindBar(QDialog):
    centerOn = Signal(QGraphicsItem)

    def __init__(self, gir: OnnxGraph, parent: Union[QWidget, None] = None) -> None:
        super().__init__(parent)
        self._ui = Ui_FindBar()
        self._ui.setupUi(self)

        self._ir = gir

        self._ui.btn_find.clicked.connect(self.do_find)

        self._ui.filter_node.setChecked(True)
        self._ui.filter_io.setChecked(True)
        self._ui.filter_var.setChecked(True)

        self._ui.ret_list.itemDoubleClicked.connect(self.on_item_double_clicked)

        self.setWindowTitle('Find')

    def add_item(self, name: str, node: QGraphicsItem):
        item = QListWidgetItem(name)
        assert node is not None
        ir = node.ir
        if isinstance(ir, OnnxNode):
            item.setIcon(QIcon(":/img/node.png"))
        elif isinstance(ir, OnnxVar):
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

    def clear_item(self):
        self._ui.ret_list.clear()

    @Slot()
    def do_find(self):
        self.clear_item()

        data_name = self._ui.le_name.text()
        data_type = self._ui.find_mod.currentText()

        if data_type == 'Has':
            def fn(s):
                return data_name in s
        elif data_type == 'StartWith':
            def fn(s):
                return s.startswith(data_name)
        elif data_type == 'EndsWith':
            def fn(s):
                return s.endswith(data_name)
        elif data_type == 'Regex':
            def fn(s):
                return re.fullmatch(data_name, s) is not None
        else:
            raise RuntimeError(f'Unknown find type: {data_type}')

        if self._ui.filter_node.isChecked():
            for n in self._ir.nodes:
                if fn(n.name):
                    self.add_item(n.name, n.read_ext('bind_gnode'))
        if self._ui.filter_io.isChecked():
            for v in self._ir.input:
                if fn(v.name):
                    self.add_item(v.name, v.read_ext('bind_gnode_src'))
            for v in self._ir.output:
                if fn(v.name):
                    self.add_item(v.name, v.read_ext('bind_gnode_dst'))
        if self._ui.filter_var.isChecked():
            for v in self._ir.variables:
                if fn(v.name):
                    self.add_item(v.name, v.read_ext('bind_gedge'))

    @Slot(QListWidgetItem)
    def on_item_double_clicked(self, item: QListWidgetItem):
        it = item.data(Qt.ItemDataRole.UserRole)
        if it is not None:
            self.centerOn.emit(it)
