from onnxeditor.ir.port import OnnxImport, OnnxExport
import onnx.checker
import onnx

import sys

assert len(sys.argv) == 3

imp = OnnxImport()
exp = OnnxExport()

m = onnx.load(sys.argv[1])

# onnx.checker.check_model(m)

m = imp(m)

m = exp(m)

onnx.save(m, sys.argv[2])

# onnx.checker.check_model(m)
