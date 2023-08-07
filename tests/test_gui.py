from onnxeditor.gui import entry
from onnxeditor.ir import Model
# from onnxeditor.ir.port import OnnxImport
import numpy as np


# imp = OnnxImport()
# m = imp('/Users/opluss/Downloads/resnet18-v1-7.onnx')
m = Model()

g = m.graph

n0t0 = g.addNode('name0', 'opt0')

n0t0.setAttr('a0', "sdfasfs")
n0t0.setAttr('sadf', 123)
n0t0.setAttr('cc', [1, 2, 3])
n0t0.setAttr('data', np.array([1, 2, 34]))

# n1t1 = g.addNode('name1', 'opt1')
# n2t1 = g.addNode('name2', 'opt1')
# n3t2 = g.addNode('name3', 'opt2')

g.markInput('v0')

c0 = g.addVariable('c0')
c0.data = np.array([1, 2, 3])

n0t0.input = ['v0']
n0t0.output = ['v1']

g.markOutput('v1')

# n1t1.input = ['c0']
# n1t1.output = ['v2']
# n2t1.input = ['v1', 'v2']
# n2t1.output = ['v3', 'v4']
# n3t2.input = ['v3', 'v2']
# n3t2.output = ['v5']


# g.markOutput('c0')
# g.markOutput('v2')
# g.markOutput('v5')

# print(m)

entry(m)
