from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QGraphicsScene, QMenu, QGraphicsSceneContextMenuEvent, QDialog
from PySide6.QtCore import Signal, Slot, Qt, QRectF, QPointF
from ...ir import Graph, Node, Variable
from .node import GraphNode
from .normal_node import NormalGraphNode
from .io_node import IOGraphNode
from .edge import GraphEdge
from typing import List, Union
from grandalf.graphs import graph_core as GC
from grandalf.graphs import Graph as GG
from grandalf.graphs import Vertex as NN
from grandalf.graphs import Edge as EE
from grandalf.layouts import SugiyamaLayout
from ..ui import IOSummary, NodeSummary
import time
from typing import Union


class GraphScene(QGraphicsScene):
    def __init__(self, ir: Graph, parent=None):
        super().__init__(parent)
        self._ir: Graph = ir
        self._normal_node = []
        self._io_node = []
        self._edge = []
        if self._ir is not None:
            def del_item(o: Union[Node, Variable]):
                n: GraphNode = o.read_ext('bind_gnode')
                n.setPos(0, 0)
                self.removeItem(n)
            self._ir.var_add_callback = self.bind_edge
            self._ir.node_add_callback = self.bind_node
            self._ir.node_del_callback = del_item
            self._ir.var_mark_input_callback = self.bind_node
            self._ir.var_mark_output_callback = self.bind_node
            self._ir.var_unmark_input_callback = del_item
            self._ir.var_unmark_output_callback = del_item
            # init var before node
            # because signal connect in node
            for v in self._ir.variables:
                self.bind_edge(v)
            for v in self._ir.input:
                self.bind_node(v)
            for v in self._ir.output:
                self.bind_node(v)
            for n in self._ir.nodes:
                self.bind_node(n)

    def bind_node(self, ir: Union[Node, Variable]):
        if isinstance(ir, Node):
            if ir.op_type in ['Constant']:
                # we will skip display constant
                return None
            n = NormalGraphNode(ir, self)
            self._normal_node.append(n)
        else:
            assert isinstance(ir, Variable)
            n = IOGraphNode(ir, self)
            self._io_node.append(n)
        assert ir.read_ext('bind_gnode') is None
        ir.set_ext('bind_gnode', n)
        self.addItem(n)
        n.connectToEdge()
        return n

    def bind_edge(self, ire: Variable):
        e = GraphEdge(ire, self)
        self._edge.append(e)
        assert ire.read_ext('bind_gedge') is None
        ire.set_ext('bind_gedge', e)
        self.addItem(e)
        return e

    def layout(self):
        ts = time.time()
        print('cvt to layout ir')
        N = {n.ir.id: NN(n) for n in self._normal_node}
        N.update({n.ir.id: NN(n) for n in self._io_node})
        if len(N) == 0:
            print('skip layout because empty graph')
            return (None, None)
        E = []
        for n in N.values():
            n = n.data
            if isinstance(n, NormalGraphNode):
                src = n.ir.prevNodes
                dst = n.ir.nextNodes
                for v in n.ir.input:
                    if v.isInput:
                        src.append(v)
                for v in n.ir.output:
                    if v.isOutput:
                        dst.append(v)
            elif isinstance(n, IOGraphNode):
                src = n.ir.src
                dst = n.ir.dst
            else:
                raise RuntimeError(f'Unexcept type: {type(n)}')
            for s in src:
                if s.id in N:
                    E.append(
                        EE(N[s.id], N[n.ir.id], data=f'{s.name} -> {n.ir.name}'))
            for d in dst:
                if d.id in N:
                    E.append(
                        EE(N[n.ir.id], N[d.id], data=f'{n.ir.name} -> {d.name}'))
        print('cvt done:', time.time() - ts, 's')
        ts = time.time()
        print('gen gc')
        g = GG(list(N.values()), E)
        print('gen done:', time.time() - ts, 's')
        print('graph_core num:', len(g.C))
        ts = time.time()
        print('layout start')
        for n in N.values():
            rect = n.data.boundingRect()
            assert rect is not None

            class HWView(object):
                w, h = rect.width(), rect.height()
            n.view = HWView()
            # print(n.data.ir.name, n.view.w, n.view.h)
        sug = SugiyamaLayout(g.C[0])
        sug.init_all()
        sug.draw()
        box = QRectF()
        first_node = None
        for n in g.C[0].sV:
            x, y = n.view.xy
            w = n.view.w
            h = n.view.h
            x = x - w / 2
            y = y - h / 2
            this_box = QRectF(x, y, w, h)
            box |= this_box
            # print(n.data.ir.name, x, y)
            n.data.setPos(x, y)
            if first_node is None:
                first_node = n.data
            # print(n.data.ir.name, n.data.pos())
        print('layout done:', time.time() - ts, 's')
        return (box, first_node)

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:
        super().contextMenuEvent(event)

        def add_node():
            n = self.addNodeDialog()
            if n is not None:
                n.setPos(event.scenePos())

        def add_io(input):
            def f():
                n = self.addIODialog(input)
                if n is not None:
                    n.setPos(event.scenePos())
            return f
        m = QMenu()
        new_node_act = m.addAction("New Node")
        new_node_act.triggered.connect(add_node)
        new_input_act = m.addAction("New Input")
        new_input_act.triggered.connect(add_io(True))
        new_output_act = m.addAction("New Output")
        new_output_act.triggered.connect(add_io(False))
        m.exec(event.screenPos())
        event.accept()

    def addNode(self, name, op_type, inputs, outputs, attrs):
        n = self._ir.addNode(name, op_type)
        n.input = inputs
        n.output = outputs
        n.clearAttr()
        for k, v in attrs.items():
            n.setAttr(k, v)
        assert n.read_ext('bind_gnode') is not None
        return n.read_ext('bind_gnode')

    def addIO(self, name, shape, type, input):
        v = self._ir.getVariable(name)
        v.shape = shape
        v.type = type
        if input:
            self._ir.markInput(v)
        else:
            self._ir.markOutput(v)
        assert v.read_ext('bind_gedge') is not None
        assert v.read_ext('bind_gnode') is not None
        return v.read_ext('bind_gnode')

    def delNode(self, n: NormalGraphNode):
        assert isinstance(n, NormalGraphNode)
        n.ir.removeFromGraph()
        # below was skip because we using update edge by graph ir callback
        # n.setPos(0, 0)
        # self.removeItem(n)

    def delIO(self, n: IOGraphNode):
        assert isinstance(n, IOGraphNode)
        if n.ir.isInput:
            n.ir.unMarkInput()
        if n.ir.isOutput:
            n.ir.unMarkOutput()
        # below was skip because we using update edge by graph ir callback
        # n.setPos(0, 0)
        # self.removeItem(n)

    def addNodeDialog(self):
        dialog = NodeSummary()
        dialog.setWindowTitle('Add Node')
        ret = dialog.exec()
        if ret == QDialog.DialogCode.Accepted:
            ret = dialog.getRet()
            return self.addNode(ret['name'], ret['op_type'], ret['inputs'], ret['output'], ret['attrs'])
        return None

    def addIODialog(self, input=True):
        dialog_name = 'Input' if input else 'Output'
        dialog = IOSummary()
        dialog.setWindowTitle('Add ' + dialog_name)
        ret = dialog.exec()
        if ret == QDialog.DialogCode.Accepted:
            ret = dialog.getRet()
            return self.addIO(ret['name'], ret['shape'], ret['type'], input)
        return None

    def keyPressEvent(self, event: QKeyEvent) -> None:
        super().keyPressEvent(event)
        if event.isAccepted():
            return
        if event.key() in [Qt.Key.Key_Delete, Qt.Key.Key_Backspace]:
            for item in self.selectedItems():
                if isinstance(item, NormalGraphNode):
                    self.delNode(item)
                elif isinstance(item, IOGraphNode):
                    self.delIO(item)
