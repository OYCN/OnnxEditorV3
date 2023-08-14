# OnnxEditorV3

It is a qt based onnx editor by pure python

## Install

``` bash
# install from pypip
pip install onnxeditor
# or install by git link
pip install -U git+https://github.com/OYCN/OnnxEditorV3.git
```

## Support List

 -  Graph Input / Output
    - Add / Remove
    - Edit shape
 - Graph Node
   - Add / Remove
   - Edit `name`
   - Edit `op_type`
   - Edit `attribute`
     - **Not support edit tensor yet**

## Todo List

 - [ ] Support Tensor Edit

## Knowed Issue

 > Sorry, we not test for all case :<
 
### Qt Error

**Q:**

> qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.
> This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.
>
> Available platform plugins are: linuxfb, eglfs, minimal, minimalegl, vnc, wayland, vkkhrdisplay, offscreen, wayland-egl, xcb.

**A:**

reference: https://bugreports.qt.io/browse/PYSIDE-2306

```bash
sudo apt install libxcb-cursor0
```
