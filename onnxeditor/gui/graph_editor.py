from typing import Union
from PySide6.QtGui import QPainter, QPen, QColor, QKeyEvent, QWheelEvent, QTransform
from PySide6.QtWidgets import QGraphicsView, QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QRect, QLineF, QPointF, Slot
from ..ir import Graph
from .graphics.scene import GraphScene
import math
from .ui import FindBar


class GraphEditor(QGraphicsView):
    def __init__(self, ir: Graph, parent=None):
        super().__init__(parent)
        self.viewport().setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, False)
        self._ir: Graph = ir

        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        s = GraphScene(self._ir, self)
        box, first_n = s.layout()
        self.setScene(s)

        if box is not None:
            box.adjust(0, -50, 0, 50)
            self.setSceneRect(box)
            self.setScale(1.5)
        if first_n is not None:
            self.centerOn(first_n)

        self.setBackgroundBrush(QColor(53, 53, 53))

        self._find_bar = FindBar(self._ir, self)
        self._find_bar.centerOn.connect(self.focusOn)

    @property
    def name(self):
        return self._ir.name

    def drawBackground(self, painter: QPainter, rect: Union[QRectF, QRect]) -> None:
        super().drawBackground(painter, rect)

        def drawGrid(gridStep):
            windowRect = self.rect()
            tl = self.mapToScene(windowRect.topLeft())
            br = self.mapToScene(windowRect.bottomRight())
            left = math.floor(tl.x() / gridStep - 0.5)
            right = math.floor(br.x() / gridStep + 1.0)
            bottom = math.floor(tl.y() / gridStep - 0.5)
            top = math.floor(br.y() / gridStep + 1.0)
            for xi in range(left, right+1):
                painter.drawLine(
                    QLineF(xi * gridStep, bottom * gridStep, xi * gridStep, top * gridStep))
            for yi in range(bottom, top+1):
                painter.drawLine(QLineF(left * gridStep, yi *
                                 gridStep, right * gridStep, yi * gridStep))

        pfine = QPen(QColor(60, 60, 60), 1.0)
        painter.setPen(pfine)
        drawGrid(15)
        pfine = QPen(QColor(25, 25, 25), 1.0)
        painter.setPen(pfine)
        drawGrid(150)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Shift:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        return super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Shift:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        return super().keyReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta()
        if delta.y() == 0:
            event.ignore()
            return super().wheelEvent(event)
        d = delta.y() / abs(delta.y())
        if d > 0.0:
            self.scaleUp()
        else:
            self.scaleDown()
        # return super().wheelEvent(event)

    def scaleUp(self):
        step = 1.2
        factor = step ** 1
        t = self.transform()
        if (t.m11() > 2):
            return
        self.scale(factor, factor)

    def scaleDown(self):
        step = 1.2
        factor = step ** (-1.0)
        t = self.transform()
        if t.m11() < 0.15:
            return
        self.scale(factor, factor)

    def scaleExtremeUp(self):
        t = self.transform()
        self.scaleUp()
        while t != self.transform():
            self.scaleUp()

    def scaleExtremeDown(self):
        t = self.transform()
        self.scaleDown()
        while t != self.transform():
            self.scaleDown()

    def setScale(self, scale):
        self.setTransform(QTransform(scale, 0, 0, scale, 0, 0))

    def expand(self, f):
        rectTmp = self.scene().sceneRect()
        ptTopLeft = rectTmp.topLeft()
        ptBottomRight = rectTmp.bottomRight()
        rect = self.rect()
        ptW_H = f * QPointF(rect.width(), rect.height())
        ptTopLeft -= ptW_H
        ptBottomRight += ptW_H
        rectTmp.setTopLeft(ptTopLeft)
        rectTmp.setBottomRight(ptBottomRight)
        self.scene().setSceneRect(rectTmp)
        self.update()

    def centerTop(self):
        hBar = self.horizontalScrollBar()
        vBar = self.verticalScrollBar()
        hBar.setValue(hBar.minimum() + (hBar.maximum() - hBar.minimum()) / 2)
        vBar.setValue(vBar.minimum())
        self.update()

    @Slot(QGraphicsItem)
    def focusOn(self, obj: QGraphicsItem, clean_selected=True):
        if clean_selected:
            self.scene().clearSelection()
        self.centerOn(obj)
        obj.setSelected(True)
        self.scene().setFocusItem(obj, Qt.FocusReason.MenuBarFocusReason)

    @Slot()
    def displayFindBar(self):
        self._find_bar.show()
