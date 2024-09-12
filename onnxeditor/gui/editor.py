from typing import Union
from PySide6.QtGui import QPainter, QPen, QColor, QKeyEvent, QWheelEvent, QTransform
from PySide6.QtWidgets import QGraphicsView, QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QRect, QLineF, QPointF, Slot
from ..ir import OnnxModel
from .graphics.scene import GraphScene
import math
from .ui import FindBar, ModelEditor


class Editor(QGraphicsView):
    def __init__(self, irm: OnnxModel, parent=None):
        super().__init__(parent)
        self.viewport().setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, False)
        self._irm: OnnxModel = irm

        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        s = GraphScene(self._irm.graph, self)
        box, first_n = s.layout()
        self.setScene(s)

        if box is not None:
            box.adjust(0, -50, 0, 50)
            self.setSceneRect(box)
            self.set_scale(1.5)
        if first_n is not None:
            self.centerOn(first_n)

        self.setBackgroundBrush(QColor(53, 53, 53))

        self._find_bar = FindBar(self._irm.graph, self)
        self._find_bar.centerOn.connect(self.focus_on)

    def get_model_ir(self):
        return self._irm

    def drawBackground(self, painter: QPainter, rect: Union[QRectF, QRect]) -> None:
        super().drawBackground(painter, rect)

        def draw_grid(grid_step):
            window_rect = self.rect()
            tl = self.mapToScene(window_rect.topLeft())
            br = self.mapToScene(window_rect.bottomRight())
            left = math.floor(tl.x() / grid_step - 0.5)
            right = math.floor(br.x() / grid_step + 1.0)
            bottom = math.floor(tl.y() / grid_step - 0.5)
            top = math.floor(br.y() / grid_step + 1.0)
            for xi in range(left, right + 1):
                painter.drawLine(
                    QLineF(
                        xi * grid_step,
                        bottom * grid_step,
                        xi * grid_step,
                        top * grid_step,
                    )
                )
            for yi in range(bottom, top + 1):
                painter.drawLine(
                    QLineF(
                        left * grid_step,
                        yi * grid_step,
                        right * grid_step,
                        yi * grid_step,
                    )
                )

        pen = QPen(QColor(60, 60, 60), 1.0)
        painter.setPen(pen)
        draw_grid(15)
        pen = QPen(QColor(25, 25, 25), 1.0)
        painter.setPen(pen)
        draw_grid(150)

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
            self.scale_up()
        else:
            self.scale_down()
        # return super().wheelEvent(event)

    def scale_up(self):
        step = 1.2
        factor = step**1
        t = self.transform()
        if t.m11() > 2:
            return
        self.scale(factor, factor)

    def scale_down(self):
        step = 1.2
        factor = step ** (-1.0)
        t = self.transform()
        if t.m11() < 0.15:
            return
        self.scale(factor, factor)

    def scale_extreme_up(self):
        t = self.transform()
        self.scale_up()
        while t != self.transform():
            self.scale_up()

    def scale_extreme_down(self):
        t = self.transform()
        self.scale_down()
        while t != self.transform():
            self.scale_down()

    def set_scale(self, scale):
        self.setTransform(QTransform(scale, 0, 0, scale, 0, 0))

    def expand(self, f):
        rect_tmp = self.scene().sceneRect()
        pt_top_left = rect_tmp.topLeft()
        pt_bottom_right = rect_tmp.bottomRight()
        rect = self.rect()
        pt_w_h = f * QPointF(rect.width(), rect.height())
        pt_top_left -= pt_w_h
        pt_bottom_right += pt_w_h
        rect_tmp.setTopLeft(pt_top_left)
        rect_tmp.setBottomRight(pt_bottom_right)
        self.scene().setSceneRect(rect_tmp)
        self.update()

    def center_top(self):
        h_bar = self.horizontalScrollBar()
        v_bar = self.verticalScrollBar()
        h_bar.setValue(h_bar.minimum() + (h_bar.maximum() - h_bar.minimum()) / 2)
        v_bar.setValue(v_bar.minimum())
        self.update()

    @Slot(QGraphicsItem)
    def focus_on(self, obj: QGraphicsItem, clean_selected=True):
        if clean_selected:
            self.scene().clearSelection()
        self.centerOn(obj)
        obj.setSelected(True)
        self.scene().setFocusItem(obj, Qt.FocusReason.MenuBarFocusReason)

    @Slot()
    def display_find_bar(self):
        self._find_bar.show()

    @Slot()
    def show_model_editor_dialog(self):
        dialog = ModelEditor(self._irm, self)
        dialog.exec()
        ret = dialog.getRet()
        for k, v in ret.items():
            setattr(self._irm, k, v)
