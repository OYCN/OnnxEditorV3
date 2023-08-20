from ..base import Model, Graph, Variable, DataBase, Node, TensorType
from typing import TYPE_CHECKING, Union, List
import onnx
import onnx.numpy_helper
import numpy as np

# copy from https://github.com/NVIDIA/TensorRT/blob/release/8.6/tools/onnx-graphsurgeon/onnx_graphsurgeon/importers/onnx_importer.py

# Maps values from the AttributeType enum to their string representations, e.g., {1: "FLOAT"}
ATTR_TYPE_MAPPING = dict(zip(onnx.AttributeProto.AttributeType.values(
), onnx.AttributeProto.AttributeType.keys()))

# Maps an ONNX attribute to the corresponding Python property
ONNX_PYTHON_ATTR_MAPPING = {
    "FLOAT": "f",
    "INT": "i",
    "STRING": "s",
    "TENSOR": "t",
    "GRAPH": "g",
    "FLOATS": "floats",
    "INTS": "ints",
    "STRINGS": "strings",
}


def get_onnx_tensor_shape(onnx_tensor: Union[onnx.ValueInfoProto, onnx.TensorProto]) -> List[int]:
    shape = []
    if isinstance(onnx_tensor, onnx.TensorProto):
        shape = onnx_tensor.dims
    else:
        if onnx_tensor.type.tensor_type.HasField("shape"):
            shape = []
            for dim in onnx_tensor.type.tensor_type.shape.dim:
                if dim.HasField("dim_param"):
                    shape.append(dim.dim_param)
                elif dim.HasField("dim_value"):
                    shape.append(dim.dim_value)
                else:
                    shape.append(None)
    return shape


def get_onnx_tensor_dtype(onnx_tensor: Union[onnx.ValueInfoProto, onnx.TensorProto]) -> np.dtype:
    if isinstance(onnx_tensor, onnx.TensorProto):
        onnx_type = onnx_tensor.data_type
    else:
        onnx_type = onnx_tensor.type.tensor_type.elem_type
    if onnx_type in onnx.mapping.TENSOR_TYPE_TO_NP_TYPE:
        return onnx.mapping.TENSOR_TYPE_TO_NP_TYPE[onnx_type]
    else:
        raise NotImplementedError(f'{onnx_type} not handled')


class LazyData(DataBase):
    def __init__(self, tensor, location) -> None:
        self._tensor = tensor
        self._data = tensor
        self._location = location
        self._type = get_onnx_tensor_dtype(tensor)
        self._shape = tuple(get_onnx_tensor_shape(tensor))
        super().__init__()

    @property
    def type(self):
        return self._type

    @property
    def shape(self):
        return self._shape

    @property
    def location(self):
        return self._location

    @property
    def tensor(self):
        return self._tensor

    def getNp(self) -> np.ndarray:
        if not isinstance(self._data, np.ndarray):
            self._data = np.array(onnx.numpy_helper.to_array(self._data))
            assert self._type == self._data.dtype
            assert self._shape == self._data.shape
        return self._data


class OnnxImport:
    def __init__(self, pass_fns: list = list()) -> None:
        if not isinstance(pass_fns, (list, tuple)):
            pass_fns = [pass_fns]
        self._pass_fns = pass_fns

    def __call__(self, m) -> Model:
        irm = Model()

        if isinstance(m, str):
            m = onnx.load(m)

        assert isinstance(m, onnx.ModelProto), (type(m), m)

        self.parse_model(m, irm)

        for fn in self._pass_fns:
            ret = fn(irm)
            assert ret[0], ret[1]

        return irm

    def parse_model(self, src: onnx.ModelProto, dst: Model):
        dst.opset_import = {}
        for v in src.opset_import:
            assert v.domain not in dst.opset_import
            dst.opset_import[v.domain] = v.version
        for field in ['ir_version', 'producer_name', 'producer_version', 'domain', 'model_version', 'doc_string']:
            setattr(dst, field, getattr(src, field) if src.HasField(
                field) else None)
        self.parse_graph(src.graph, dst.graph)

    def parse_graph(self, src: onnx.GraphProto, dst: Graph):
        dst.name = src.name
        dst.doc_string = src.doc_string if src.HasField("doc_string") else None
        for v in src.output:
            irv = self.parse_value_info(v, dst)
            dst.markOutput(irv)
        const_var_name = []
        for v in src.initializer:
            irv = self.parse_tensor(v, dst)
            const_var_name.append(irv.name)
        for v in src.value_info:
            self.parse_value_info(v, dst)
        for n in src.node:
            self.parse_node(n, dst)
        for v in src.input:
            irv = self.parse_value_info(v, dst)
            if irv.name not in const_var_name:
                dst.markInput(irv)
        return dst

    def parse_value_info(self, src: onnx.ValueInfoProto, dst: Graph):
        v = dst.getVariable(src.name)
        if not v.isConstant:
            try:
                v.type = get_onnx_tensor_dtype(src)
            except NotImplementedError as e:
                print(f'get err when handle dtype, skiped: {e}')
                v.type = TensorType.kNone
            v.shape = get_onnx_tensor_shape(src)
        return v

    def parse_tensor(self, src: onnx.TensorProto, dst: Union[Graph, None]):
        if dst is None:
            v = Variable(None, src.name)
        else:
            v = dst.getVariable(src.name)
        data_location = int(src.data_location) if src.HasField(
            "data_location") else None
        v.data = LazyData(src, data_location)
        return v

    def parse_node(self, src: onnx.NodeProto, dst: Graph):
        n = dst.addNode(src.name, src.op_type)
        n.input = [str(v) for v in src.input]
        n.output = [str(v) for v in src.output]
        n.domain = src.domain if src.HasField("domain") else None
        n.doc_string = src.doc_string if src.HasField("doc_string") else None
        n.clearAttr()
        for attr in src.attribute:
            if attr.type in ATTR_TYPE_MAPPING:
                attr_str = ATTR_TYPE_MAPPING[attr.type]
                if attr_str in ONNX_PYTHON_ATTR_MAPPING:
                    assert attr.name not in n.attrs
                    processed = getattr(
                        attr, ONNX_PYTHON_ATTR_MAPPING[attr_str])
                    if attr_str == "STRING":
                        processed = processed.decode()
                    elif attr_str == "TENSOR":
                        processed = self.parse_tensor(processed, None)
                    elif attr_str == "GRAPH":
                        g = Graph()
                        self.parse_graph(processed, g)
                        processed = g
                    elif attr_str == "FLOATS" or attr_str == "INTS":
                        processed = list(processed)
                    elif attr_str == "STRINGS":
                        processed = [p.decode() for p in processed]
                    n.attrs[attr.name] = processed
                elif attr_str == 'UNDEFINED':
                    print(
                        f'warning: UNDEFINED attr got in node: {n.name}, op_type: {n.op_type}')
                    pass
                else:
                    raise KeyError(
                        f'attr not handled, maybe new ir: {attr_str}, node: {n.name}, op_type: {n.op_type}')
            else:
                raise KeyError(f'attr not handled, maybe new ir: {attr.type}')
        return n
