from typing import Any, Optional, Union, Dict
import PySide6.QtGui
from PySide6.QtWidgets import QLabel, QGraphicsItem, QGraphicsWidget, QGraphicsProxyWidget, QGraphicsSceneHoverEvent, QGraphicsSceneMouseEvent, QStyleOptionGraphicsItem, QWidget, QGraphicsLinearLayout, QGraphicsTextItem, QGraphicsGridLayout
from PySide6.QtCore import Signal, Qt, QRectF, QLineF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics, QPalette, QBrush
from ...ir import Variable, Node
import math
import abc


class GraphNode(QGraphicsWidget):
    _id_counter: int = 0

    pos_move = Signal(list)
    io_change = Signal(list)

    def __init__(self, parent=None):
        super().__init__()

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(2)

        self._hovered = False

        self._id = GraphNode._id_counter
        GraphNode._id_counter += 1

    @property
    def id(self):
        return self._id

    def layoutWith(self, op_type: str, name: Union[str, None], attrs: Union[None, Dict[str, Any]]):
        layout = QGraphicsLinearLayout(Qt.Orientation.Vertical, self)

        def gen_txt(txt, size, weight, color=QColor("black")):
            label = QLabel(txt)
            label.setFont(QFont('Monospace', size, weight))
            palette = label.palette()
            palette.setColor(QPalette.ColorRole.WindowText, color)
            palette.setColor(QPalette.ColorRole.Window,
                             Qt.GlobalColor.transparent)
            label.setPalette(palette)
            proxy = QGraphicsProxyWidget()
            proxy.setWidget(label)
            return proxy

        op_type_size = 14
        op_type_weight = QFont.Weight.Bold
        if name is not None:
            layout.addItem(
                gen_txt(name, 14, QFont.Weight.Bold), QColor(255, 255, 255))
            op_type_weight = QFont.Weight.Medium
            op_type_size = 13

        assert op_type is not None
        layout.addItem(gen_txt(op_type, op_type_size,
                       op_type_weight, QColor(255, 255, 255)))

        if attrs is not None:
            if len(attrs) > 0:
                attrs_layout = QGraphicsGridLayout()
                for i, (k, v) in enumerate(attrs.items()):
                    key_item = gen_txt(
                        k, 10, QFont.Weight.Normal, QColor(255, 255, 255))
                    attrs_layout.addItem(key_item, i, 0)

                    if isinstance(v, Variable):
                        v = f'{v.type.value}<{v.shape}>'
                    value_item = gen_txt(
                        str(v), 10, QFont.Weight.Thin, QColor(255, 255, 255))
                    attrs_layout.addItem(value_item, i, 1)
                layout.addItem(attrs_layout)

        self.setLayout(layout)
        self.adjustSize()

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._hovered = True
        self.update()
        return super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._hovered = False
        self.update()
        return super().hoverLeaveEvent(event)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        return super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(event)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.pos_move.emit([self])
        return super().itemChange(change, value)

    def paint(self, painter: QPainter, option, widget=None):
        color = QColor(255, 165, 0) if self.isSelected(
        ) else QColor(255, 255, 255)
        width = 1.5 if self._hovered else 1
        painter.setPen(QPen(color, width))
        painter.setBrush(QBrush(QColor(100, 100, 100)))
        painter.drawRoundedRect(self.boundingRect(), 10, 10)

    def connectToEdge(self): ...
