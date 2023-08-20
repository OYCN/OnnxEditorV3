from typing import Any, Optional, TYPE_CHECKING
import PySide6.QtGui
from PySide6.QtWidgets import QGraphicsItem, QGraphicsSceneHoverEvent, QGraphicsSceneMouseEvent, QStyleOptionGraphicsItem, QWidget, QDialog
from PySide6.QtCore import Signal, Qt, QRectF, QLineF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics
from ...ir import Variable
import math
from .node import GraphNode
from ..ui import IOSummary

if TYPE_CHECKING:
    from .edge import GraphEdge


class IOGraphNode(GraphNode):

    def __init__(self, ir: Variable, parent=None):
        super().__init__(parent)
        self._ir: Variable = ir

        self._title = None
        self._border = QRectF()

        self.layoutWith(self._ir.name, None, None)

    @property
    def ir(self):
        return self._ir

    def connectToEdge(self):
        e: GraphEdge = self._ir.read_ext('bind_gedge')
        self.pos_move.connect(e.needUpdate)
        self.io_change.connect(e.needUpdate)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        dialog_name = 'Input' if self._ir.isInput else 'Output'
        assert self._ir.graph is not None
        dialog = IOSummary(self._ir, self._ir.graph.variables)
        dialog.setWindowTitle('Edit ' + dialog_name)
        ret = dialog.exec()
        if ret == QDialog.DialogCode.Accepted:
            ret = dialog.getRet()
            assert self._ir.name == ret['name']
            self._ir.shape = ret['shape']
            self._ir.type = ret['type']
            self.layoutWith(self._ir.name, None, None)
        return super().mouseDoubleClickEvent(event)
