import onnx
import onnx.helper
from ..base import Model, Graph, Variable, Node, TensorType
from .imp import LazyData
import numpy as np


class OnnxExport:
    def __call__(self, ir: Model, path: str = None) -> onnx.ModelProto:
        assert isinstance(ir, Model)
        m = self.parse_model(ir)
        if path is not None:
            onnx.save(m, path)
        return m

    def parse_model(self, ir: Model):
        g = self.parse_graph(ir.graph)
        kwargs = {'opset_imports': []}
        for k, v in ir.opset_import.items():
            kwargs['opset_imports'].append(
                onnx.OperatorSetIdProto(domain=k, version=v))
        for field in ['ir_version', 'producer_name', 'producer_version', 'domain', 'model_version', 'doc_string']:
            v = getattr(ir, field)
            if v is not None:
                kwargs[field] = v
        m = onnx.helper.make_model(g, **kwargs)
        return m

    def parse_graph(self, ir: Graph):
        nodes = [self.parse_node(n) for n in ir.nodes]
        inputs = [self.parse_value_info(v) for v in ir.input]
        outputs = [self.parse_value_info(v) for v in ir.output]
        initializer = [self.parse_tensor(
            v) for v in ir.variables if v.isConstant and v.used]
        value_info = [self.parse_value_info(
            v) for v in ir.variables if not v.isConstant and v.used]
        value_info = [v for v in value_info if v is not None]
        inputs.extend([self.parse_value_info(v)
                      for v in ir.variables if v.isConstant and v.used])
        g = onnx.helper.make_graph(
            nodes=nodes,
            name=ir.name,
            inputs=inputs,
            outputs=outputs,
            initializer=initializer,
            doc_string=ir.doc_string,
            value_info=value_info,
        )
        return g

    def parse_value_info(self, ir: Variable):
        if ir.type is None or ir.type is TensorType.kNone:
            t = 0
        else:
            t = onnx.helper.np_dtype_to_tensor_dtype(
                np.dtype(ir.type.toNumpy()))
        value_info = onnx.helper.make_tensor_value_info(
            ir.name, t, ir.shape, ir.doc_string)
        return value_info

    def parse_tensor(self, ir: Variable):
        data = ir.data
        assert data is not None
        if isinstance(data, LazyData):
            tensor = data.tensor
        else:
            tensor = onnx.numpy_helper.from_array(data.getNp())
            if data.location is not None:
                tensor.data_location = data.location
        tensor.name = ir.name
        return tensor

    def parse_node(self, ir: Node):
        node = onnx.helper.make_node(
            ir.op_type,
            inputs=[v.name for v in ir.input],
            outputs=[v.name for v in ir.output],
            name=ir.name,
            domain=ir.domain,
            doc_string=ir.doc_string
        )
        for key, val in ir.attrs.items():
            if isinstance(val, Variable):
                val = self.parse_tensor(val)
            elif isinstance(val, Graph):
                val = self.parse_graph(val)
            else:
                pass
            node.attribute.extend([onnx.helper.make_attribute(key, val)])
        return node
