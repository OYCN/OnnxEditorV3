from typing import Dict
from .obj import IRObj
from .graph import Graph


class Model(IRObj):
    def __init__(self) -> None:
        super().__init__()

        self.ir_version: int = None
        self.opset_import: Dict[str, int] = {}
        self.producer_name: str = None
        self.producer_version: str = None
        self.domain: str = None
        self.model_version: int = None
        self.doc_string: str = None
        self.graph: Graph = Graph()

        self.displayAttr('ir_version')
        self.displayAttr('opset_import')
        self.displayAttr('producer_name')
        self.displayAttr('producer_version')
        self.displayAttr('domain')
        self.displayAttr('model_version')
        self.displayAttr('doc_string')
        self.displayAttr('graph')
