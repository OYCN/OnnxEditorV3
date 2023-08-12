from onnxeditor.ir.port import OnnxImport, OnnxExport
from onnxeditor.ir.opt import pass_const_to_var
import onnx.checker
import onnx
import sys

assert len(sys.argv) == 3

imp = OnnxImport(pass_const_to_var)
exp = OnnxExport()

m = onnx.load(sys.argv[1])

onnx.checker.check_model(m)

m = imp(m)

m = exp(m)

onnx.save(m, sys.argv[2])

onnx.checker.check_model(m)
