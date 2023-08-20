from typing import Optional, Any, Union
import PySide6.QtCore
from PySide6.QtWidgets import QDialog, QWidget, QListWidget, QListWidgetItem, QAbstractItemView, QHeaderView, QComboBox, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QStackedLayout, QCompleter
from PySide6.QtCore import Qt, Slot, Signal
from ....ir import Node, Variable, NativeData, Graph
from .ui_nodesummary import Ui_NodeSummary
from ..datainspector import DataInspector
import re
import numpy as np


class AttrValue(QWidget):
    def __init__(self, v, parent: Union[QWidget, None] = None) -> None:
        super().__init__(parent)
        self._edit = QLineEdit()
        self._edit.setPlaceholderText("-")
        self._btn = QPushButton('Edit Tensor')

        self._data = None
        if isinstance(v, Variable):
            self._data = v.data
        if isinstance(v, (list, tuple)):
            self._edit.setText(','.join([str(vv) for vv in v]))
        else:
            self._edit.setText(str(v))

        self._layout = QStackedLayout()
        self._layout.addWidget(self._edit)
        self._layout.addWidget(self._btn)

        self.setLayout(self._layout)

        self._btn.clicked.connect(self.set_data)

    @Slot(str)
    def needSwitch(self, v):
        if v == 'Tensor':
            self.showBtn()
        else:
            self.showEdit()

    def showEdit(self):
        self._layout.setCurrentWidget(self._edit)

    def showBtn(self):
        self._layout.setCurrentWidget(self._btn)

    def parseElem(self, txt):
        if re.fullmatch(f'^-?\d+$', txt) is not None:
            return int(txt)
        elif re.fullmatch(f'^-?\d+\.\d*$', txt) is not None:
            return float(txt)
        else:
            return str(txt)

    def getVal(self):
        w = self._layout.currentWidget()
        if w is self._edit:
            txt = self._edit.text()
            if len(txt) == 0:
                return ''
            if re.fullmatch(f'^-?\d+$', txt) is not None:
                return int(txt)
            elif re.fullmatch(f'^-?\d+\.\d*$', txt) is not None:
                return float(txt)
            elif ',' in txt and re.fullmatch(f'^((-?[0-9a-zA-Z]+),?)*$', txt) is not None:
                ret = re.findall(r'(-?[0-9a-zA-Z]+)', txt)
                return [self.parseElem(r) for r in ret]
            else:
                return txt
        else:
            if self._data is None:
                return np.array([])
            return self._data

    @Slot()
    def set_data(self):
        dialog = DataInspector(display_name=False)
        dialog.setWindowTitle('Set Data Attribute')
        ret = dialog.exec()
        if ret == QDialog.DialogCode.Accepted:
            ret = dialog.getRet()[0]
            self._data = NativeData(ret)


class NodeSummary(QDialog):
    def __init__(self, nir: Union[Node, None] = None, g: Union[Graph, None] = None, parent: Union[QWidget, None] = None) -> None:
        super().__init__(parent)
        self._ui = Ui_NodeSummary()
        self._ui.setupUi(self)

        if g is None:
            if nir is not None:
                if nir.graph is not None:
                    g = nir.graph

        if g is not None:
            self._cmp = QCompleter([v.name for v in g.variables], self)
        else:
            self._cmp = None

        header = ['name', 'type', 'value']
        self._ui.inputs_list_widget.setAlternatingRowColors(True)
        self._ui.attr_tabel_widget.setColumnCount(len(header))
        self._ui.attr_tabel_widget.verticalHeader().hide()
        self._ui.attr_tabel_widget.verticalHeader().setDefaultSectionSize(15)
        self._ui.attr_tabel_widget.setHorizontalHeaderLabels(header)
        self._ui.attr_tabel_widget.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self._ui.attr_tabel_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection)
        self._ui.attr_tabel_widget.setAlternatingRowColors(True)
        self._ui.attr_tabel_widget.horizontalHeader().setSectionResizeMode(0,
                                                                           QHeaderView.ResizeMode.Stretch)
        self._ui.attr_tabel_widget.horizontalHeader().setSectionResizeMode(1,
                                                                           QHeaderView.ResizeMode.Stretch)
        self._ui.attr_tabel_widget.horizontalHeader().setSectionResizeMode(2,
                                                                           QHeaderView.ResizeMode.Stretch)

        self._ui.inputs_add.clicked.connect(
            lambda _: self.addItem(self._ui.inputs_list_widget, ""))
        self._ui.inputs_del.clicked.connect(
            lambda _: self.delItem(self._ui.inputs_list_widget))
        self._ui.outputs_add.clicked.connect(
            lambda _: self.addItem(self._ui.outputs_list_widget, ""))
        self._ui.outputs_del.clicked.connect(
            lambda _: self.delItem(self._ui.outputs_list_widget))
        self._ui.attr_add.clicked.connect(
            lambda _: self.addRow("", '', False))
        self._ui.attr_del.clicked.connect(lambda _: self.delRow())

        if nir is not None:
            self._ui.name_edit.setText(nir.name)
            self._ui.op_type_edit.setText(nir.op_type)
            for i in nir.input:
                self.addItem(self._ui.inputs_list_widget, i.name)
            for o in nir.output:
                self.addItem(self._ui.outputs_list_widget, o.name)
            for k, v in nir.attrs.items():
                self.addRow(k, v, isinstance(v, Variable))

    def addItem(self, lw: QListWidget, name: str):
        item = QListWidgetItem()
        edit = QLineEdit(name)
        edit.setPlaceholderText('-')
        if self._cmp is not None:
            edit.setCompleter(self._cmp)
        lw.addItem(item)
        lw.setItemWidget(item, edit)
        lw.setCurrentItem(item)

    def delItem(self, lw: QListWidget):
        for item in lw.selectedItems():
            lw.removeItemWidget(item)

    def addRow(self, key: str, value: Any, istensor: bool = False):
        row = self._ui.attr_tabel_widget.rowCount()
        self._ui.attr_tabel_widget.insertRow(row)
        # type
        box = QComboBox()
        box.addItems(['Scalar(s)', 'Tensor'])
        box.setCurrentIndex(1 if istensor else 0)
        self._ui.attr_tabel_widget.setCellWidget(row, 1, box)
        # name
        # item = QTableWidgetItem(key)
        # item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        # self._ui.attr_tabel_widget.setItem(row, 0, item)
        item = QLineEdit(key)
        item.setPlaceholderText("-")
        self._ui.attr_tabel_widget.setCellWidget(row, 0, item)
        # value
        item = AttrValue(value)
        if istensor:
            item.showBtn()
        else:
            item.showEdit()
        self._ui.attr_tabel_widget.setCellWidget(row, 2, item)
        box.currentTextChanged.connect(item.needSwitch)

    def delRow(self):
        row_id = [item.row()
                  for item in self._ui.attr_tabel_widget.selectedItems()]
        row_id = sorted(row_id, reverse=True)
        for id in row_id:
            self._ui.attr_tabel_widget.removeRow(id)

    def getRet(self):
        ins_w = self._ui.inputs_list_widget
        outs_w = self._ui.outputs_list_widget
        attrs_w = self._ui.attr_tabel_widget
        ret = {
            'name': self._ui.name_edit.text(),
            'op_type': self._ui.op_type_edit.text(),
            'inputs': [ins_w.itemWidget(ins_w.item(i)).text() for i in range(ins_w.count())],
            'output': [outs_w.itemWidget(outs_w.item(i)).text() for i in range(outs_w.count())],
            'attrs': {}
        }
        for r in range(attrs_w.rowCount()):
            # k = attrs_w.item(r, 0).text()
            k = attrs_w.cellWidget(r, 0).text()
            # t_w = attrs_w.cellWidget(r, 1)
            v_w = attrs_w.cellWidget(r, 2)
            assert k not in ret['attrs']
            ret['attrs'][k] = v_w.getVal()
        return ret
