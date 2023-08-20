from typing import Any, Optional, TYPE_CHECKING
import PySide6.QtGui
from PySide6.QtWidgets import QGraphicsItem, QGraphicsSceneHoverEvent, QGraphicsSceneMouseEvent, QStyleOptionGraphicsItem, QWidget, QDialog
from PySide6.QtCore import Signal, Qt, QRectF, QLineF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics
from ...ir import Node, Variable
import math
from .node import GraphNode
from ..ui import NodeSummary

if TYPE_CHECKING:
    from .edge import GraphEdge


class NormalGraphNode(GraphNode):

    def __init__(self, ir: Node, parent=None):
        super().__init__(parent)
        self._ir: Node = ir

        self._attr_layout = []
        self._line = QLineF()
        self._border = QRectF()

        self.layoutWith(self._ir.op_type, None, self._ir.attrs)

        def io_change(v: Node):
            assert v.read_ext('bind_gnode') == self
            self.connectToEdge()
            self.io_change.emit([self])

        self._ir.input_change_callback = io_change
        self._ir.output_change_callback = io_change

    @property
    def ir(self):
        return self._ir

    def connectToEdge(self):
        '''
        here, we just connect the signal, edge will auto disconnect the unreachable link
        '''
        for i in self._ir.input:
            e: GraphEdge = i.read_ext('bind_gedge')
            self.pos_move.connect(e.needUpdate)
            self.io_change.connect(e.needUpdate)
        for o in self._ir.output:
            e: GraphEdge = o.read_ext('bind_gedge')
            self.pos_move.connect(e.needUpdate)
            self.io_change.connect(e.needUpdate)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        dialog = NodeSummary(self._ir)
        dialog.setWindowTitle('Edit Node')
        ret = dialog.exec()
        if ret == QDialog.DialogCode.Accepted:
            ret = dialog.getRet()
            self._ir.name = ret['name']
            self._ir.op_type = ret['op_type']
            self._ir.input = ret['inputs']
            self._ir.output = ret['output']
            self._ir.clearAttr()
            for k, v in ret['attrs'].items():
                self._ir.setAttr(k, v)
            self.layoutWith(self._ir.op_type, None, self._ir.attrs)
        return super().mouseDoubleClickEvent(event)
