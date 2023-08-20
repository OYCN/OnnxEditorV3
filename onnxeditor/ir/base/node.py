from typing import TYPE_CHECKING, List, Dict, Any
from .obj import IRObj
import json
import numpy as np
import copy

if TYPE_CHECKING:
    from .graph import Graph
    from .variable import Variable


class Node(IRObj):
    def __init__(self, graph: 'Graph', name: str, op_type: str) -> None:
        super().__init__()

        self.name: str = name
        self.op_type: str = op_type
        self.domain: str = None
        self.doc_string: str = None
        self._attrs: Dict[str: Any] = {}
        self._input: List[str] = []
        self._output: List[str] = []

        self._graph: 'Graph' = graph

        self.displayAttr('name')
        self.displayAttr('op_type')
        self.displayAttr('domain')
        self.displayAttr('doc_string')
        self.displayAttr('attrs')
        self.displayAttr('_input', name='input')
        self.displayAttr('_output', name='output')

        self.input_change_callback = None
        self.output_change_callback = None
        self.node_remove_callback = None

        self._ext['bind_gnode'] = None

    @property
    def input(self):
        if self._graph is None:
            return []
        return [self._graph.getVariable(v) for v in self._input]

    @input.setter
    def input(self, new_ins):
        if self._graph is None:
            raise RuntimeError(
                f'Can not set input for no graph node, using self._input for setting/reading by str')
        new_ins = [self._graph.getVariable(v) if isinstance(
            v, str) else v for v in new_ins]
        old_ins = [self._graph.getVariable(v) for v in self._input]
        self._input = [v.name for v in new_ins]
        old_ins = set([v.name for v in old_ins])
        new_ins = set([v.name for v in new_ins])
        diff_old_ins = old_ins - new_ins
        diff_new_ins = new_ins - old_ins
        if len(diff_old_ins) + len(diff_new_ins) > 0:
            self._graph._emit_node_input_change(
                self, diff_old_ins, diff_new_ins)
            if self.input_change_callback is not None:
                self.input_change_callback(self)

    @property
    def output(self):
        if self._graph is None:
            return []
        return [self._graph.getVariable(v) for v in self._output]

    @output.setter
    def output(self, new_outs):
        if self._graph is None:
            raise RuntimeError(
                f'Can not set output for no graph node, using self._output for setting/reading by str')
        new_outs = [self._graph.getVariable(v) if isinstance(
            v, str) else v for v in new_outs]
        old_outs = [self._graph.getVariable(v) for v in self._output]
        self._output = [v.name for v in new_outs]
        old_outs = set([v.name for v in old_outs])
        new_outs = set([v.name for v in new_outs])
        diff_old_outs = old_outs - new_outs
        diff_new_outs = new_outs - old_outs
        if len(diff_old_outs) + len(diff_new_outs) > 0:
            self._graph._emit_node_output_change(
                self, diff_old_outs, diff_new_outs)
            if self.output_change_callback is not None:
                self.output_change_callback(self)

    @property
    def attrs(self):
        return self._attrs

    def clearAttr(self):
        self._attrs.clear()

    def setAttr(self, key, val):
        if isinstance(val, np.ndarray):
            from .variable import Variable
            val = Variable(None, '', data=val)
        self._attrs[key] = val

    @property
    def prevNodes(self):
        return [n for v in self.input for n in v._src_nodes]

    @property
    def nextNodes(self):
        return [n for v in self.output for n in v._dst_nodes]

    @property
    def graph(self):
        return self._graph

    @graph.setter
    def graph(self, g):
        assert self._graph is None
        self._graph = g
        self._graph._emit_node_output_change(
            self, [], self._output)
        self._graph._emit_node_input_change(
            self, [], self._input)

    def removeFromGraph(self):
        assert self._graph is not None
        self._graph._emit_node_output_change(
            self, self._output, [])
        self._graph._emit_node_input_change(
            self, self._input, [])
        self._graph._nodes.remove(self)
        callback = self._graph.node_del_callback
        self._graph = None
        if self.node_remove_callback is not None:
            callback = self.node_remove_callback
        if callback is not None:
            callback(self)

    def copyOut(self):
        new = copy.copy(self)
        new._graph = None
        return copy.deepcopy(new)
