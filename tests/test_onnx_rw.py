from onnxeditor.ir.port import OnnxImport, OnnxExport
import onnx.checker
import onnx

imp = OnnxImport()
exp = OnnxExport()

m = onnx.load('/Users/opluss/Downloads/resnet18-v1-7.onnx')

onnx.checker.check_model(m)

m = imp(m)

m = exp(m)

onnx.save(m, '/Users/opluss/Downloads/resnet18-v1-7.cp.onnx')

onnx.checker.check_model(m)
