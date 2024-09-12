import onnx
import onnx.helper
import numpy as np

from .onnx_common import OnnxModel, OnnxGraph, OnnxNode, OnnxVar, LazyData, TensorType


class OnnxExport:
    def __call__(self, ir: OnnxModel, path: str = None) -> onnx.ModelProto:
        assert isinstance(ir, OnnxModel)
        print("[OnnxExport] start topo sort")
        ir.graph.topo_sort()
        print("[OnnxExport] topo sort done")

        def var_size():
            irset = set()
            for n in ir.graph.nodes:
                for i in n.inputs:
                    irset.add(i.unqn)
                for o in n.outputs:
                    irset.add(o.unqn)
            return len(irset)

        print(f"[OnnxExport] before merge var, var len = {var_size()}")
        ir.graph.merge_var_by("name")
        print(f"[OnnxExport] after merge var by `name`, var len = {var_size()}")
        m = self.parse_model(ir)
        if path is not None:
            onnx.save(m, path)
        return m

    def parse_model(self, ir: OnnxModel):
        g = self.parse_graph(ir.graph)
        kwargs = {"opset_imports": []}
        for d, v in ir.opset_import:
            kwargs["opset_imports"].append(onnx.OperatorSetIdProto(domain=d, version=v))
        for field in [
            "ir_version",
            "producer_name",
            "producer_version",
            "domain",
            "model_version",
            "doc_string",
        ]:
            v = getattr(ir, field)
            if v is not None:
                kwargs[field] = v
        m = onnx.helper.make_model(g, **kwargs)
        return m

    def parse_graph(self, ir: OnnxGraph):
        nodes = [self.parse_node(n) for n in ir.nodes]
        inputs = [self.parse_value_info(v) for v in ir.inputs if v.type is not None]
        outputs = [self.parse_value_info(v) for v in ir.outputs if v.type is not None]
        initializer = [
            self.parse_tensor(v) for v in ir.variables if v.isConstant and v.isUsed
        ]
        value_info = [
            self.parse_value_info(v)
            for v in ir.variables
            if not v.isConstant
            and v.isUsed
            and v not in ir.inputs
            and v not in ir.outputs
            and v.type is not None
        ]
        value_info = [v for v in value_info if v is not None]
        inputs.extend(
            [
                self.parse_value_info(v)
                for v in ir.variables
                if v.isConstant and v.isUsed and v.type is not None
            ]
        )
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

    def parse_value_info(self, ir: OnnxVar):
        assert ir.type is not None
        if ir.type is TensorType.kNone:
            t = 0
        else:
            t = onnx.helper.np_dtype_to_tensor_dtype(np.dtype(ir.type.toNumpy()))
        value_info = onnx.helper.make_tensor_value_info(
            ir.name, t, ir.shape, ir.doc_string
        )
        return value_info

    def parse_tensor(self, ir: OnnxVar):
        data = ir.data
        assert data is not None
        if isinstance(data, LazyData):
            tensor = data.tensor
        else:
            ndarray = data.getNp()
            if len(ndarray.shape) == 0:
                tensor = onnx.numpy_helper.from_array(ndarray.reshape(1))
                tensor.ClearField("dims")
            else:
                tensor = onnx.numpy_helper.from_array(ndarray)
            if data.location is not None:
                tensor.data_location = data.location
        tensor.name = ir.name
        return tensor

    def parse_node(self, ir: OnnxNode):
        node = onnx.helper.make_node(
            ir.op_type,
            inputs=[v.name for v in ir.inputs],
            outputs=[v.name for v in ir.outputs],
            name=ir.name,
            domain=ir.domain,
            doc_string=ir.doc_string,
        )

        def parse_attr(val):
            if isinstance(val, OnnxVar):
                val = self.parse_tensor(val)
            elif isinstance(val, OnnxGraph):
                val = self.parse_graph(val)
            else:
                assert isinstance(val, (float, int, str)), type(val)
            return val

        for key, val in ir.attrs.items():
            if isinstance(val, (list, tuple)):
                val = [parse_attr(v) for v in val]
            else:
                val = parse_attr(val)
            node.attribute.extend([onnx.helper.make_attribute(key, val)])
        return node
