### Undo/Redo support for Maya Python API 2.0

Leverage the API in your Python scripts, without losing out on the ability to undo or redo.

**Features**

- Undo and redo for arbitrary API calls
- Intermix `apiundo` with native undo from calls via `cmds` or `PyMEL`
- Automatically aggregates calls to `cmds` with `apiundo`
- Distributed as a single Python module

**Limitations**

> Help wanted

1. Single level of undo + redo. Once redone, it can no longer be undone.
2. Undoing something differently to how it was done can result in fatal errors.
3. Using `cmds` during an undo can put Maya's undo queue in an inconsistent state, leading to fatale errors. [More details](http://help.autodesk.com/cloudhelp/2018/ENU/Maya-Tech-Docs/CommandsPython/undoInfo.html)

<br>

### Usage

Running the below snippet will cause the newly created transform to be deleted. Redoing will cause it to be re-created.

1. Make API calls
2. Commit an undo function to history

**Example**

```python
from maya.api import OpenMaya as om
import apiundo

mod = om.MDagModifier()
mod.createNode("transform")
mod.doIt()

apiundo.commit(
    undo=mod.undoIt,
    redo=mod.doIt
)
```

Keep in mind that you are responsible for the undo to actually undo what you intend it to. `apiundo` cannot know what you are asking it to call, anything could happen.

<br>

### Install

apiundo is a single Python module, compatible **Maya 2015** and above on Windows, Linux and MacOS.

1. Download [`apiundo.py`](https://raw.githubusercontent.com/mottosso/apiundo/master/apiundo.py)
2. Save in your `$HOME/maya/scripts` directory

Or anywhere on your `PYTHONPATH`.

<br>

### How it works

An `MPxCommand` plug-in is registered and called whenever an undo operations is added to the queue. The call itself does nothing and is meant to represent API calls made before it. Calling it means Maya queues the subsequent undo and redo operations for when you next undo and redo.

<br>

### Background

Maya implements undo/redo via subclasses of `MPxCommand`. Each command implements `doIt`, `undoIt` and `redoIt` which Maya manages for you such that when you ask it to undo, it calls the corresponding `undoIt` method of your subclass.

```python
class ExampleCmd(om.MPxCommand):
    def doIt(self, args):
        self.displayInfo("Doing..")

    def undoIt(self):
        self.displayInfo("Undoing..")

    def redoIt(self):
        self.displayInfo("Redoing..")

    def isUndoable(self):
        return True
```

However this doesn't account for when you require use of the API independently.

```python
from maya.api import OpenMaya as om
node = om.MFnDagNode().create("transform")
```

This call for example is [~9 times faster](#performance) than an equivalent call to `pymel.core.createNode()` and [~3 times faster](#performance) than `maya.cmds.createNode()`, but cannot be undone.

<br>

### Performance

As an aside and justification of the example in [Background](#background), this is how the 3x number was found.

```python
# Tested on Maya 2015 and 2017
import timeit

from maya import OpenMaya as om1
from maya.api import OpenMaya as om2
from maya import cmds
from pymel import core as pm

def Test(func):
	return min(timeit.repeat(
		func,
		setup=lambda: cmds.file(new=True, force=True),
		number=1000,
		repeat=3
	))

fn1 = om1.MFnDagNode()
fn2 = om2.MFnDagNode()

timings = dict()
timings["mel"] = Test(lambda: mel.eval("createNode \"transform\""))
timings["cmds"] = Test(lambda: cmds.createNode("transform"))
timings["pm"] = Test(lambda: pm.createNode("transform"))
timings["om1"] = Test(lambda: fn1.create("transform"))
timings["om2"] = Test(lambda: fn2.create("transform"))

print("Timings")
for method, timing in timings.items():
	print("%s: %.2f ms" % (method, timing * 1000))
```












