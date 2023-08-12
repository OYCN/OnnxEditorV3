from ..base import Model
from ..port import OnnxImport

from typing import Tuple


def pass_const_to_var(m: Model) -> Tuple[bool, str]:
    assert isinstance(m, Model)
    g = m.graph
    for n in g.nodes:
        if n.op_type == 'Constant':
            assert len(n.attrs) == 1
            k, v = list(n.attrs.items())[0]
            assert len(n.output) == 1
            out = n.output[0]
            if k == 'value':
                out.data = v.data
            else:
                raise NotImplementedError(
                    f'we not impl the elements type for constant node, the attr is {k} : {v}')
            g.delNode(n)
    return True, 'succ'
