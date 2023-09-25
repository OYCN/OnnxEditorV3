from typing import TYPE_CHECKING, Dict, Any, Set, List, Union, Tuple
from types import FunctionType
from enum import Enum, auto
import numpy as np
import json
from .obj import IRObj
import abc
import copy

if TYPE_CHECKING:
    from .node import Node
    from .graph import Graph


class TensorType(Enum):
    kNone = 'None'
    kBOOL = 'Bool'
    kFP16 = 'Float16'
    kFP32 = 'Float32'
    kFP64 = 'Float64'
    kINT8 = 'Int8'
    kINT32 = 'Int32'
    kINT64 = 'Int64'

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
        assert self in dt2np, f'not handled {self} yet'
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


class Variable(IRObj):
    def __init__(self, graph: Union['Graph', None], name: str, shape: list = list(), type: Union[TensorType, np.dtype] = TensorType.kNone, data: Union[None, np.ndarray, DataBase] = None) -> None:
        super().__init__()

        assert isinstance(name, str)
        self._name: str = name
        self._shape: list = shape
        self._type: TensorType = None
        self._data: DataBase = None
        self.doc_string = ''

        self.type = type
        self.data = data

        self._src_nodes: Set['Node'] = set()
        self._dst_nodes: Set['Node'] = set()

        self._graph: Union['Graph', None] = graph

        self._marked_variable = False

        self.displayAttr('name')
        self.displayAttr('shape')
        self.displayAttr('type')
        self.displayAttr('_data', name='data')
        self.displayAttr('doc_string')

        self._ext['bind_gedge'] = None
        self._ext['bind_gnode_src'] = None
        self._ext['bind_gnode_dst'] = None
        self._ext['bind_gnode_last'] = None

    @property
    def graph(self):
        return self._graph

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, v):
        assert self._graph is None
        self._name = v

    @property
    def data(self):
        return self._data

    @property
    def location(self):
        return self._data.location

    @data.setter
    def data(self, d):
        if isinstance(d, np.ndarray):
            d = NativeData(d)
        if d is None:
            self._data = None
        else:
            assert isinstance(d, DataBase)
            self._data = d

    @property
    def type(self):
        if self._data is None:
            return self._type
        else:
            return TensorType.fromNumpy(self._data.type)

    @type.setter
    def type(self, t):
        assert self._data is None, f'{self.name} already is a constant, can not set type explicitly'
        if t is None or isinstance(t, TensorType):
            self._type = t
        else:
            self._type = TensorType.fromNumpy(t)

    @property
    def shape(self):
        if self._data is None:
            return self._shape
        else:
            return self._data.shape

    @shape.setter
    def shape(self, s):
        assert self._data is None
        self._shape = tuple(s)

    @property
    def src(self):
        return self._src_nodes.copy()

    @property
    def dst(self):
        return self._dst_nodes.copy()

    @property
    def used(self):
        return (len(self._src_nodes) + len(self._dst_nodes)) > 0 or self._graph is None

    @property
    def canBeInput(self):
        return not self.isConstant and len(self._src_nodes) == 0 and self.used and self._graph is not None

    @property
    def maybeOutput(self):
        return len(self._dst_nodes) == 0 and self.used and self._graph is not None

    @property
    def isInput(self):
        if self._graph is None:
            return False
        else:
            return self in self._graph.input

    @property
    def isOutput(self):
        if self._graph is None:
            return False
        else:
            return self in self._graph.output

    @property
    def isConstant(self):
        return self.data is not None and not self._marked_variable

    def markVariable(self):
        self._marked_variable = True

    def removeFromGraph(self):
        assert not self.used
        del self._graph._variables[self.name]
        self._graph = None

    def copyOut(self):
        new = copy.copy(self)
        new._graph = None
        new._src_nodes = set()
        new._dst_nodes = set()
        return copy.deepcopy(new)

    def markInput(self, *args, **kwargs):
        assert self._graph is not None
        self._graph.markInput(self, *args, **kwargs)

    def unMarkInput(self, *args, **kwargs):
        assert self._graph is not None
        self._graph.unMarkInput(self.name, *args, **kwargs)

    def markOutput(self, *args, **kwargs):
        assert self._graph is not None
        self._graph.markOutput(self, *args, **kwargs)

    def unMarkOutput(self, *args, **kwargs):
        assert self._graph is not None
        self._graph.unMarkOutput(self.name, *args, **kwargs)
