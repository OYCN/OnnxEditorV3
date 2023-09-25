from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
import os

GEN_LIST = [
    ("onnxeditor/gui/res", "res.qrc", "res.py"),
    ("onnxeditor/gui/ui/iosummary", "iosummary.ui", "ui_iosummary.py"),
    ("onnxeditor/gui/ui/nodesummary", "nodesummary.ui", "ui_nodesummary.py"),
    ("onnxeditor/gui/ui/datainspector", "datainspector.ui", "ui_datainspector.py"),
]


class BuildQtFileCommand(build_py):
    def run(self):
        for item in GEN_LIST:
            if item[1].endswith('.qrc'):
                os.system(
                    f'cd {item[0]} && pyside6-rcc {item[1]} -o {item[2]}')
            elif item[1].endswith('.ui'):
                os.system(
                    f'cd {item[0]} && pyside6-uic {item[1]} -o {item[2]}')
            else:
                raise NotImplementedError(f'Not handled suffix: {item[1]}')
        build_py.run(self)


setup(
    name='onnxeditor',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'pyside6',
        'grandalf',
        'onnx',
    ],
    python_requires='>=3.6',
    author='oPluss',
    author_email='opluss@qq.com',
    description='A Qt base onnx editor',
    long_description='A Qt base onnx editor',
    url='https://github.com/OYCN/OnnxEditorV3',
    cmdclass={
        'build_py': BuildQtFileCommand,
    },
    entry_points={
        'console_scripts': [
            'onnxeditor=onnxeditor:main',
        ],
    },
)
