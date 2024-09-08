from typing import Union, List
import onnx
import onnx.numpy_helper
import numpy as np

from .onnx_common import (
    get_onnx_tensor_dtype,
    get_onnx_tensor_shape,
    TensorType,
    LazyData,
    OnnxModel,
    OnnxGraph,
    OnnxNode,
    OnnxVar,
    ATTR_TYPE_MAPPING,
    ONNX_PYTHON_ATTR_MAPPING,
)


def try_guess_attr_type(attr):
    guess_list = []
    for t, f in ONNX_PYTHON_ATTR_MAPPING.items():
        if len(f) > 1 and f.endswith("s"):
            if len(getattr(attr, f)) > 0:
                guess_list.append(t)
        elif attr.HasField(f):
            guess_list.append(t)
    if len(guess_list) > 0:
        if len(guess_list) == 1:
            print(f"[OnnxImport] guess the attr type is {guess_list[0]}")
            return guess_list[0]
        else:
            print(
                f"[OnnxImport] the attr type has more candidate, we return the first: {guess_list}"
            )
            return guess_list[0]
    return "UNDEFINED"


class OnnxImport:
    def __init__(self, pass_fns: list = list()) -> None:
        if not isinstance(pass_fns, (list, tuple)):
            pass_fns = [pass_fns]
        self._pass_fns = pass_fns

    def __call__(self, m) -> OnnxModel:
        irm = OnnxModel()

        if isinstance(m, str):
            m = onnx.load(m)

        assert isinstance(m, onnx.ModelProto), (type(m), m)

        self.parse_model(m, irm)

        for fn in self._pass_fns:
            ret = fn(irm)
            assert ret[0], ret[1]

        return irm

    def parse_model(self, src: onnx.ModelProto, dst: OnnxModel):
        dst.opset_import = []
        for v in src.opset_import:
            domain = v.domain if v.HasField("domain") else None
            version = v.version if v.HasField("version") else None
            dst.opset_import.append((domain, version))
        for field in [
            "ir_version",
            "producer_name",
            "producer_version",
            "domain",
            "model_version",
            "doc_string",
        ]:
            setattr(dst, field, getattr(src, field) if src.HasField(field) else None)
        self.parse_graph(src.graph, dst.graph)

    def parse_graph(self, src: onnx.GraphProto, dst: OnnxGraph):
        dst.name = src.name
        dst.doc_string = src.doc_string if src.HasField("doc_string") else None
        for v in src.output:
            irv = self.parse_value_info(v, dst)
            dst.add_output(irv)
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
                dst.add_input(irv)
        return dst

    def parse_value_info(self, src: onnx.ValueInfoProto, dst: OnnxGraph):
        v = dst.getVar(src.name)
        if v.data is not None:
            return v
        try:
            v.type = get_onnx_tensor_dtype(src)
        except NotImplementedError as e:
            print(f"get err when handle dtype, skiped: {e}")
            v.type = TensorType.kNone
        v.shape = get_onnx_tensor_shape(src)
        return v

    def parse_tensor(self, src: onnx.TensorProto, dst: Union[OnnxGraph, None]):
        if dst is None:
            v = OnnxVar(src.name)
        else:
            v = dst.getVar(src.name)
        data_location = (
            int(src.data_location) if src.HasField("data_location") else None
        )
        v.data = LazyData(src, data_location)
        return v

    def parse_node(self, src: onnx.NodeProto, dst: OnnxGraph):
        n = dst.add_node(OnnxNode(src.name, src.op_type))
        n.op_type = src.op_type
        n.inputs = [dst.getVar(v) for v in src.input]
        n.outputs = [dst.getVar(v) for v in src.output]
        n.domain = src.domain if src.HasField("domain") else None
        n.doc_string = src.doc_string if src.HasField("doc_string") else None
        for attr in src.attribute:
            if attr.type in ATTR_TYPE_MAPPING:
                attr_str = ATTR_TYPE_MAPPING[attr.type]
                if attr_str == "UNDEFINED":
                    attr_str = try_guess_attr_type(attr)
                if attr_str in ONNX_PYTHON_ATTR_MAPPING:
                    assert attr.name not in n.attrs, (attr.name, list(n.attrs.keys()))
                    processed = getattr(attr, ONNX_PYTHON_ATTR_MAPPING[attr_str])
                    if attr_str == "STRING":
                        processed = processed.decode()
                    elif attr_str == "TENSOR":
                        processed = self.parse_tensor(processed, None)
                    elif attr_str == "GRAPH":
                        g = OnnxGraph()
                        self.parse_graph(processed, g)
                        processed = g
                    elif attr_str == "FLOATS" or attr_str == "INTS":
                        processed = list(processed)
                    elif attr_str == "STRINGS":
                        processed = [p.decode() for p in processed]
                    n.attrs[attr.name] = processed
                elif attr_str == "UNDEFINED":
                    print(
                        f"warning: UNDEFINED attr got in node: {n.name}, op_type: {n.op_type}"
                    )
                    pass
                else:
                    raise KeyError(
                        f"attr not handled, maybe new ir: {attr_str}, node: {n.name}, op_type: {n.op_type}"
                    )
            else:
                raise KeyError(f"attr not handled, maybe new ir: {attr.type}")
        return n