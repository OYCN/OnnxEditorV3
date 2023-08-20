from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QGraphicsScene, QMenu, QGraphicsSceneContextMenuEvent, QDialog, QMessageBox
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
from ..ui import IOSummary, NodeSummary, DataInspector
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
            def del_nodeitem(o: Node):
                assert o.read_ext('bind_gnode') is not None
                n: GraphNode = o.read_ext('bind_gnode')
                n.setPos(0, 0)
                self.removeItem(n)

            def del_io_item(input: bool):
                def f(o: Variable):
                    n = o.read_ext(
                        'bind_gnode_src' if input else 'bind_gnode_dst')
                    n: GraphNode = o.read_ext('bind_gnode')
                    n.setPos(0, 0)
                    self.removeItem(n)
                return f

            def add_io_item(input: bool):
                def f(o: Variable):
                    self.bind_node(o, input)
                return f
            self._ir.var_add_callback = self.bind_edge
            self._ir.node_add_callback = self.bind_node
            self._ir.node_del_callback = del_nodeitem
            self._ir.var_mark_input_callback = add_io_item(True)
            self._ir.var_mark_output_callback = add_io_item(False)
            self._ir.var_unmark_input_callback = del_io_item(True)
            self._ir.var_unmark_output_callback = del_io_item(False)
            # init var before node
            # because signal connect in node
            for v in self._ir.variables:
                self.bind_edge(v)
            for v in self._ir.input:
                self.bind_node(v, True)
            for v in self._ir.output:
                self.bind_node(v, False)
            for n in self._ir.nodes:
                self.bind_node(n)

    def bind_node(self, ir: Union[Node, Variable], asinput: bool = False):
        if isinstance(ir, Node):
            if ir.op_type in ['Constant']:
                # we will skip display constant
                return None
            n = NormalGraphNode(ir, self)
            self._normal_node.append(n)
            assert ir.read_ext('bind_gnode') is None
            ir.set_ext('bind_gnode', n)
        else:
            assert isinstance(ir, Variable)
            n = IOGraphNode(ir, self)
            self._io_node.append(n)
            ir.set_ext('bind_gnode_last', n)
            if asinput:
                assert ir.read_ext('bind_gnode_src') is None
                ir.set_ext('bind_gnode_src', n)
            else:
                assert ir.read_ext('bind_gnode_dst') is None
                ir.set_ext('bind_gnode_dst', n)
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
        N = {n.id: NN(n) for n in self._normal_node}
        N.update({n.id: NN(n) for n in self._io_node})
        if len(N) == 0:
            print('skip layout because empty graph')
            return (None, None)
        E = {}
        for n in N.values():
            n = n.data
            if isinstance(n, NormalGraphNode):
                src = [nn.read_ext('bind_gnode').id for nn in n.ir.prevNodes]
                dst = [nn.read_ext('bind_gnode').id for nn in n.ir.nextNodes]
            elif isinstance(n, IOGraphNode):
                src = [nn.read_ext('bind_gnode').id for nn in n.ir.src]
                dst = [nn.read_ext('bind_gnode').id for nn in n.ir.dst]
                if n.ir.read_ext('bind_gnode_src') is not None:
                    src += [n.ir.read_ext('bind_gnode_src').id]
                if n.ir.read_ext('bind_gnode_dst') is not None:
                    dst += [n.ir.read_ext('bind_gnode_dst').id]
            else:
                raise RuntimeError(f'Unexcept type: {type(n)}')
            for s in src:
                if s in N:
                    E[(n.id, s)] = EE(N[n.id], N[s])
            for d in dst:
                if d in N:
                    E[(d, n.id)] = EE(N[d], N[n.id])
        print('cvt done:', time.time() - ts, 's')
        ts = time.time()
        print('N: ', len(N))
        print('E: ', len(E))
        print('gen gc')
        g = GG(list(N.values()), list(E.values()))
        print('gen done:', time.time() - ts, 's')
        print('graph_core num:', len(g.C))
        print('graph e num:', len(list(g.E())))
        print('graph v num:', len(list(g.V())))
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
        print('layout done:', time.time() - ts, 's')
        ts = time.time()
        print('layout appply')
        box = QRectF()
        top_node = None
        for n in g.C[0].sV:
            x, y = n.view.xy
            w = n.view.w
            h = n.view.h
            x = x - w / 2
            y = - y - h / 2
            this_box = QRectF(x, y, w, h)
            box |= this_box
            # print(n.data.ir.name, x, y)
            n.data.setPos(x, y)
            # print(n.data.ir.name, n.data.pos())
            if top_node is None:
                top_node = n.data
            else:
                if n.data.pos().y() < top_node.pos().y():
                    top_node = n.data
        print('apply done:', time.time() - ts, 's')
        top_input_node = None
        for n in self._io_node:
            if top_input_node is None:
                top_input_node = n
            else:
                if n.pos().y() < top_input_node.pos().y():
                    top_input_node = n
        first_node = top_node if top_input_node is None else top_input_node
        print(f'all done, box={box}, first_node: {first_node.pos()}')
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
        add_constant_act = m.addAction("Add Constant")
        add_constant_act.triggered.connect(self.addConstantDialog)
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
        if input:
            if v.isInput:
                QMessageBox.warning(
                    self.parent(), 'Add Failed', f'This input already exist: {v.name}')
                return
            self._ir.markInput(v)
        else:
            if v.isOutput:
                QMessageBox.warning(
                    self.parent(), 'Add Failed', f'This output already exist: {v.name}')
                return
            self._ir.markOutput(v)
        v.shape = shape
        v.type = type
        assert v.read_ext('bind_gedge') is not None
        n = v.read_ext('bind_gnode_last')
        v.set_ext('bind_gnode_last', None)
        assert n is not None
        return n

    def delNode(self, n: NormalGraphNode):
        assert isinstance(n, NormalGraphNode)
        n.ir.removeFromGraph()

    def delIO(self, n: IOGraphNode):
        assert isinstance(n, IOGraphNode)
        if n.ir.isInput:
            n.ir.unMarkInput()
        if n.ir.isOutput:
            n.ir.unMarkOutput()

    def addNodeDialog(self):
        dialog = NodeSummary(g=self._ir)
        dialog.setWindowTitle('Add Node')
        ret = dialog.exec()
        if ret == QDialog.DialogCode.Accepted:
            ret = dialog.getRet()
            return self.addNode(ret['name'], ret['op_type'], ret['inputs'], ret['output'], ret['attrs'])
        return None

    def addIODialog(self, input=True):
        dialog_name = 'Input' if input else 'Output'
        dialog = IOSummary(None, [
                           v for v in self._ir.variables if v.isInput == (not input) and v.isOutput == input])
        dialog.setWindowTitle('Add ' + dialog_name)
        ret = dialog.exec()
        if ret == QDialog.DialogCode.Accepted:
            ret = dialog.getRet()
            return self.addIO(ret['name'], ret['shape'], ret['type'], input)
        return None

    def addConstantDialog(self):
        dialog = DataInspector()
        dialog.setWindowTitle('Add Constant')
        ret = dialog.exec()
        if ret == QDialog.DialogCode.Accepted:
            data, name = dialog.getRet()
            self._ir.getVariable(name).data = data

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
