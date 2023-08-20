from typing import Dict, Any, Set, List
from types import FunctionType
import json


class TypeCheckMeta(type):
    def __setattr__(cls, name, value):
        expected_type = cls.__annotations__.get(name)
        print(f'{name} -> {expected_type}')
        if expected_type is not None and not isinstance(value, expected_type):
            raise TypeError(
                f"Expected type {expected_type} for attribute {name}, but got type {type(value)}")
        super().__setattr__(name, value)


class IRObj(metaclass=TypeCheckMeta):
    _id_map: List['IRObj'] = []

    def __init__(self) -> None:
        self._ext: Dict[str, Any] = {
            'display_attr': {},
            'strict_type': {},
        }
        self._id = len(self._id_map)
        self._id_map.append(self)

    @property
    def id(self):
        return self._id

    @staticmethod
    def getById(id):
        return IRObj._id_map[id]

    def read_ext(self, key):
        assert key in self._ext, key
        return self._ext[key]

    def set_ext(self, key, v):
        assert key in self._ext, key
        self._ext[key] = v

    def displayAttr(self, attr: str, name=None):
        if name is None:
            name = attr
        assert name not in self._ext['display_attr']
        self._ext['display_attr'][name] = attr

    def markStrictType(self, attr, type):
        assert attr not in self._ext['strict_type']
        self._ext['strict_type'][attr] = type

    def toJson(self) -> dict:
        def walk(v):
            if isinstance(v, IRObj):
                return v.toJson()
            elif isinstance(v, (set, list, tuple)):
                return type(v)([walk(vv) for vv in v])
            elif isinstance(v, dict):
                return {kk: walk(vv) for kk, vv in v.items()}
            else:
                return v
        return {k: walk(getattr(self, v)) for k, v in self._ext['display_attr'].items()}

    def __setattr__(self, name, value):
        if name != '_ext':
            if name in self._ext['strict_type']:
                if not isinstance(value, self._ext['strict_type'][name]):
                    raise TypeError(
                        f"Expected type {self._ext['strict_type'][name]} for attribute {name}, but got type {type(value)}")
        super().__setattr__(name, value)

    def __str__(self) -> str:
        def walk(v):
            if v is None:
                return None
            elif isinstance(v, dict):
                return {k: walk(v) for k, v in v.items()}
            elif isinstance(v, (float, int)):
                return v
            else:
                return str(v)
        return json.dumps(walk(self.toJson()), indent=2)

    def __repr__(self) -> str:
        return super().__repr__()
