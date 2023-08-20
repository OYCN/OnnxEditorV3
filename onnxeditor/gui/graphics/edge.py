from ...ir import Variable
from typing import List, TYPE_CHECKING, Any
from PySide6.QtCore import Signal, Qt, QRectF, QPointF, Slot
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics, QPainterPath, QPainterPathStroker
from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsSceneHoverEvent, QGraphicsSceneMouseEvent, QStyleOptionGraphicsItem, QWidget, QGraphicsPathItem
from typing import Union

if TYPE_CHECKING:
    from .node import GraphNode


class GraphEdge(QGraphicsObject):
    def __init__(self, ir: Variable, parent=None):
        super().__init__()
        self._ir: Variable = ir

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(0)

        self._hovered = False

        self._src_pts: List[QPointF] = []
        self._dst_pts: List[QPointF] = []
        self._path: QPainterPath = QPainterPath()

    @property
    def ir(self):
        return self._ir

    @Slot(list)
    def needUpdate(self, nodes: List['GraphNode']):
        assert len(nodes) == 1
        node = nodes[0]
        src_obj = [n.read_ext('bind_gnode') for n in self._ir.src if n.read_ext(
            'bind_gnode') is not None]
        dst_obj = [n.read_ext('bind_gnode') for n in self._ir.dst if n.read_ext(
            'bind_gnode') is not None]
        if self._ir.isInput:
            gn = self._ir.read_ext('bind_gnode_src')
            assert gn is not None
            src_obj += [gn]
        if self._ir.isOutput:
            gn = self._ir.read_ext('bind_gnode_dst')
            assert gn is not None
            dst_obj += [gn]
        assert all([v is not None for v in src_obj])
        assert all([v is not None for v in dst_obj])
        self.drawEdge(src_obj, dst_obj)
        if node not in src_obj + dst_obj:
            node.pos_move.disconnect(self.needUpdate)
            node.io_change.disconnect(self.needUpdate)

    def drawEdge(self, src_obj: List[QGraphicsItem], dst_obj: List[QGraphicsItem]):
        self._src_pts.clear()
        for o in src_obj:
            pos = o.pos()
            rect = o.boundingRect()
            self._src_pts.append(
                QPointF(rect.left() + rect.width() / 2, rect.bottom()) + pos)
            # print('src', o._ir.name, pos, rect, self._src_pts[-1])
        self._dst_pts.clear()
        for o in dst_obj:
            pos = o.pos()
            rect = o.boundingRect()
            self._dst_pts.append(
                QPointF(rect.left() + rect.width() / 2, rect.top()) + pos)
            # print('dst', o._ir.name, pos, rect, self._src_pts[-1])
        self._path.clear()
        for s in self._src_pts:
            for d in self._dst_pts:
                self._path.moveTo(s)
                c1 = QPointF(s.x(), (s.y() + d.y()) / 2)
                c2 = QPointF(d.x(), (s.y() + d.y()) / 2)
                self._path.cubicTo(c1, c2, d)
        self.prepareGeometryChange()
        self.update()

    def shape(self) -> QPainterPath:
        ps = QPainterPathStroker()
        pen = QPen()
        if self._hovered or self.isSelected():
            pen.setWidthF(2 * 3.0)
        else:
            pen.setWidthF(3.0)
        ps.setCapStyle(pen.capStyle())
        ps.setWidth(pen.widthF() + 10)
        ps.setJoinStyle(pen.joinStyle())
        ps.setMiterLimit(pen.miterLimit())
        p = ps.createStroke(self._path)
        for s in self._src_pts:
            p.addEllipse(s, 3.0, 3.0)
        for d in self._dst_pts:
            p.addEllipse(d, 5.0, 5.0)
        return p

    def boundingRect(self) -> QRectF:
        return self.shape().boundingRect()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Union[QWidget, None] = ...) -> None:
        painter.save()
        # line hovered
        if self._hovered or self.isSelected():
            p = QPen()
            p.setWidthF(2 * 3.0)
            p.setColor(QColor(255, 165, 0) if self.isSelected()
                       else QColor(224, 255, 255))
            painter.setPen(p)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(self._path)
        # line body
        p = QPen()
        p.setWidthF(3.0)
        if len(self._src_pts) > 1:
            p.setColor(QColor(248, 4, 2))
        else:
            p.setColor(QColor(100, 100, 100) if self.isSelected()
                       else QColor(0, 139, 139))
        painter.setPen(p)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self._path)
        # ellipse hovered
        color = QColor(255, 165, 0) if self.isSelected(
        ) else QColor(224, 255, 255)
        for s in self._src_pts:
            painter.setPen(color)
            painter.setBrush(color)
            painter.drawEllipse(s, 4.0, 4.0)
        for d in self._dst_pts:
            painter.setPen(color)
            painter.setBrush(color)
            painter.drawEllipse(d, 6.0, 6.0)
        # ellipse body
        for s in self._src_pts:
            painter.setPen(QColor(128, 128, 128))
            painter.setBrush(QColor(128, 128, 128))
            painter.drawEllipse(s, 3.0, 3.0)
        for d in self._dst_pts:
            painter.setPen(QColor(128, 128, 128))
            painter.setBrush(QColor(128, 128, 128))
            painter.drawEllipse(d, 5.0, 5.0)
        painter.restore()

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        # print('hoverEnterEvent')
        self._hovered = True
        self.update()
        return super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        # print('hoverLeaveEvent')
        self._hovered = False
        self.update()
        return super().hoverLeaveEvent(event)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            assert isinstance(value, int)
            if value == 1:
                self.setZValue(3)
            else:
                self.setZValue(0)
            self.update()
        return super().itemChange(change, value)
