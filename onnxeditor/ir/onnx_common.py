import onnx
import numpy as np
from enum import Enum
import abc
from typing import Any, Union, List, Tuple, Dict

import fkir

# copy from https://github.com/NVIDIA/TensorRT/blob/release/8.6/tools/onnx-graphsurgeon/onnx_graphsurgeon/importers/onnx_importer.py

# Maps values from the AttributeType enum to their string representations, e.g., {1: "FLOAT"}
ATTR_TYPE_MAPPING = dict(
    zip(
        onnx.AttributeProto.AttributeType.values(),
        onnx.AttributeProto.AttributeType.keys(),
    )
)

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


def get_onnx_tensor_dtype(
    onnx_tensor: Union[onnx.ValueInfoProto, onnx.TensorProto]
) -> np.dtype:
    if isinstance(onnx_tensor, onnx.TensorProto):
        onnx_type = onnx_tensor.data_type
    else:
        onnx_type = onnx_tensor.type.tensor_type.elem_type
    if onnx_type in onnx.mapping.TENSOR_TYPE_TO_NP_TYPE:
        return onnx.mapping.TENSOR_TYPE_TO_NP_TYPE[onnx_type]
    else:
        raise NotImplementedError(f"{onnx_type} not handled")


def get_onnx_tensor_shape(
    onnx_tensor: Union[onnx.ValueInfoProto, onnx.TensorProto]
) -> List[int]:
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


class TensorType(Enum):
    kNone = "None"
    kBOOL = "Bool"
    kFP16 = "Float16"
    kFP32 = "Float32"
    kFP64 = "Float64"
    kINT8 = "Int8"
    kINT32 = "Int32"
    kINT64 = "Int64"

    @staticmethod
    def fromNumpy(np_dt):
        np2dt = {
            np.float16: TensorType.kFP16,
            np.float32: TensorType.kFP32,
            np.float64: TensorType.kFP64,
            np.bool_: TensorType.kBOOL,
            np.int8: TensorType.kINT8,
            np.int32: TensorType.kINT32,
            np.int64: TensorType.kINT64,
        }
        if isinstance(np_dt, np.dtype):
            np_dt = np_dt.type
        assert np_dt in np2dt, (np_dt,)
        return np2dt[np_dt]

    def toNumpy(self):
        dt2np = {
            TensorType.kFP16: np.float16,
            TensorType.kFP32: np.float32,
            TensorType.kFP64: np.float64,
            TensorType.kBOOL: np.bool_,
            TensorType.kINT8: np.int8,
            TensorType.kINT32: np.int32,
            TensorType.kINT64: np.int64,
        }
        assert self in dt2np, f"not handled {self} yet"
        return dt2np[self]


class DataBase(abc.ABC):
    @property
    @abc.abstractmethod
    def type(self) -> np.dtype: ...

    @property
    @abc.abstractmethod
    def type(self) -> Tuple: ...

    @property
    def location(self):
        return None

    @abc.abstractmethod
    def getNp(self) -> np.ndarray: ...


class NativeData(DataBase):
    def __init__(self, data) -> None:
        assert isinstance(data, np.ndarray)
        self._data = data
        super().__init__()

    @property
    def type(self):
        return self._data.dtype

    @property
    def shape(self):
        return self._data.shape

    def getNp(self) -> np.ndarray:
        return self._data


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


class NoAddAttrBase:
    def __init__(self) -> None:
        self._inited = True

    def __setattr__(self, __name: str, __value: Any) -> None:
        if (
            not hasattr(self, __name)
            and hasattr(self, "_inited")
            and not isinstance(getattr(self.__class__, __name, None), property)
        ):
            raise RuntimeError(
                f"can not set attr for this obj, cld = {self.__class__} k = {__name}, v = {__value}"
            )
        super().__setattr__(__name, __value)


class OnnxVar(NoAddAttrBase, fkir.FkVar):
    def __init__(self, name=None) -> None:
        fkir.FkVar.__init__(self)
        self.name = name
        self.doc_string = None
        self._type = None
        self._data = None
        self._shape = None

        self._graph_bind = None
        NoAddAttrBase.__init__(self)

    @property
    def type(self):
        if self._data is not None:
            return TensorType.fromNumpy(self._data.type)
        else:
            return self._type

    @type.setter
    def type(self, v):
        assert self._data is None
        if isinstance(v, np.dtype):
            self._type = TensorType.fromNumpy(v)
        elif isinstance(v, TensorType):
            self._type = v
        else:
            raise NotImplementedError(f"Unhandled type: {type(v)}")

    @property
    def shape(self):
        if self._data is not None:
            return tuple(self._data.shape)
        else:
            return self._shape

    @shape.setter
    def shape(self, v):
        assert self._data is None
        self._shape = v

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, v):
        if not isinstance(v, (DataBase, type(None))):
            v = NativeData(v)
        self._data = v

    @property
    def isConstant(self):
        return self._data is not None

    @property
    def isUsed(self):
        return len(self.srcs) > 0 or len(self.dsts) > 0

    def __repr__(self) -> str:
        return f"[Var] {self.name}"


class OnnxNode(NoAddAttrBase, fkir.FkNode):
    def vis_label(self):
        return self.op_type

    def __init__(self, name=None, op_type=None) -> None:
        fkir.FkNode.__init__(self, allow_str_io=False)
        self.name: str = name
        self.op_type: str = op_type
        self.domain: str = None
        self.doc_string: str = None
        self.attrs: Dict[str:Any] = {}

        self._graph_bind = None
        NoAddAttrBase.__init__(self)

    def __repr__(self) -> str:
        return f"[{self.op_type}] {self.name}"


class OnnxGraph(NoAddAttrBase, fkir.FkGraph):
    def __init__(self, name=None) -> None:
        fkir.FkGraph.__init__(self, allow_str_io=False)
        self._unique_var_map = {}
        self.name: str = name
        self.doc_string: str = ""

        self._graph_bind = None
        NoAddAttrBase.__init__(self)

    def add_node(self, node=None):
        if node is None:
            node = OnnxNode()
        return super().add_node(node)

    @property
    def variables(self):
        return list(self._unique_var_map.values())

    def hasVar(self, v):
        if isinstance(v, str):
            return v in self._unique_var_map
        elif isinstance(v, OnnxVar):
            return v.name in self._unique_var_map
        else:
            raise NotImplementedError(type(v))

    def getVar(self, v):
        if isinstance(v, str):
            v = self._unique_var_map.get(v, OnnxVar(name=v))
            self._unique_var_map[v.name] = v
            return v
        else:
            raise NotImplementedError(type(v))

    def debug_vis(self, path):
        g = self.to_networkx()
        import networkx as nx

        gv = nx.nx_agraph.to_agraph(g)
        gv.draw(path, prog="dot")


class OnnxModel(NoAddAttrBase):
    def __init__(self) -> None:
        self.ir_version: int = 0
        self.opset_import: List[(str, int)] = []
        self.producer_name: str = ""
        self.producer_version: str = ""
        self.domain: str = None
        self.model_version: int = None
        self.doc_string: str = None
        self.graph = OnnxGraph()
        NoAddAttrBase.__init__(self)
