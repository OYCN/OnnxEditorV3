from onnxeditor.ir.base import Model
import numpy as np

m = Model()

m.producer_name = 123

'''
in0 -> |n0| --> |
                |->|n1| -> out0
     |-> |n2| ->|
in1 -|          |
     |-> |n3| ->|
         |    \-> out1
const0 ->|
'''

const0 = m.graph.addVariable('const0')
const0.data = np.array([1, 2, 3])

n0 = m.graph.addNode('n0', 'n0')
n1 = m.graph.addNode('n1', 'n1')
n2 = m.graph.addNode('n2', 'n2')
n3 = m.graph.addNode('n3', 'n3')

n0.input = ['in0']
n0.output = ['n0_out']
n1.input = [
    'n0_out',
    'n2_out',
    'out1',
]
n1.output = ['out0']
n2.input = ['in1']
n2.output = ['n2_out']
n3.input = ['in1', 'const0']
n3.output = ['out1']

m.graph.markOutput('out0')
m.graph.markOutput('out1')

m.graph.autoMarkInput()

print(m)
