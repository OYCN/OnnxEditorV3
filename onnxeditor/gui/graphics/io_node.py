from typing import TYPE_CHECKING
from PySide6.QtWidgets import QGraphicsSceneMouseEvent, QDialog
from PySide6.QtCore import QRectF
from ...ir import OnnxVar
from .node import GraphNode
from ..ui import IOSummary

if TYPE_CHECKING:
    from .edge import GraphEdge


class IOGraphNode(GraphNode):

    def __init__(self, ir: OnnxVar, parent=None):
        super().__init__(parent)
        self._ir: OnnxVar = ir

        self._title = None
        self._border = QRectF()

        self.layoutWith(self._ir.name, None, None)

    @property
    def ir(self):
        return self._ir

    def connectToEdge(self):
        e: GraphEdge = self._ir.read_ext("bind_gedge")
        self.pos_move.connect(e.needUpdate)
        self.io_change.connect(e.needUpdate)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        dialog_name = "Input" if self._ir.isInput else "Output"
        assert self._ir.graph is not None
        dialog = IOSummary(self._ir, self._ir.graph.variables)
        dialog.setWindowTitle("Edit " + dialog_name)
        ret = dialog.exec()
        if ret == QDialog.DialogCode.Accepted:
            ret = dialog.getRet()
            assert self._ir.name == ret["name"]
            self._ir.shape = ret["shape"]
            self._ir.type = ret["type"]
            self.layoutWith(self._ir.name, None, None)
        return super().mouseDoubleClickEvent(event)
