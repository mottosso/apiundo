"""Commit to Maya's internal Undo queue

Example:
    >>> mod = om.MDagModifier()
    >>> mod.createNode("transform")
    >>> mod.doIt()

    >>> apiundo.commit(
    ...     undo=mod.undoIt,
    ...     redo=mod.doIt
    ... )
    ...

Following this, undo will cause the newly created transform to
be deleted, redoing will cause it to be re-created.

How it works:
    An MPxCommand plug-in is registered and called whenever an
    undo operations is added to the queue. The call itself does
    nothing and is meant to represent API calls made before it.
    Calling it means Maya queues the subsequent undo and redo
    operations for when you next undo and redo.

Features:
    - Undo and redo any arbitrary command
    - Intermix API undo with native undo from calls via `cmds` or `PyMEL`
    - Distributed as a single Python module

Limitations:
    1. Single level of undo + redo.
        Once redone, it can no longer be undone.
    2. Undoing something differently to how it was done can result
        in fatal errors.
    3. Using `cmds` during an undo can put Maya's undo queue in
        an inconsistent state, leading to fatale errors

"""

import os
import sys

from maya import cmds
from maya.api import OpenMaya as om


def maya_useNewAPI():
    pass


# As far as a Maya plug-in is concerned, __name__ is "__builtin__"
# but since this module must be imported prior to loading the plug-in
# we know that it already exists in memory. We use that as a shared
# resource for keeping track of history.
shared = sys.modules["apiundo"]
shared.undoHistory = list()
shared.redoHistory = list()


def commit(undo, redo=lambda: None):
    """Commit `undo` and `redo` to history

    Arguments:
        undo (func): Call this function on next undo
        redo (func, optional): Like `undo`, for for redo

    """

    shared.undoHistory.append(undo)
    shared.redoHistory.append(redo)

    # Let Maya know that something is undoable
    cmds.apiUndo()


def install():
    cmds.loadPlugin(__file__, quiet=True)


def uninstall():
    cmds.unloadPlugin(os.path.basename(__file__))


def reinstall():
    # Plug-in may exist in undo queue and
    # therefore cannot be unloaded until flushed.
    state = cmds.undoInfo(state=True, query=True)
    cmds.undoInfo(state=False)
    cmds.undoInfo(state=state)

    uninstall()
    sys.modules.pop(__name__)
    module = __import__(__name__)
    module.install()
    return module


class apiUndo(om.MPxCommand):
    def doIt(self, args):
        pass

    def undoIt(self):
        self.displayInfo("Undoing..")
        func = shared.undoHistory.pop()
        func()

    def redoIt(self):
        self.displayInfo("Redoing..")
        func = shared.redoHistory.pop()
        func()

    def isUndoable(self):
        # Without this, the above undoIt and redoIt will not be called
        return True


def initializePlugin(plugin):
    pluginFn = om.MFnPlugin(plugin)
    pluginFn.registerCommand(
        apiUndo.__name__,
        apiUndo
    )


def uninitializePlugin(plugin):
    pluginFn = om.MFnPlugin(plugin)
    pluginFn.deregisterCommand(apiUndo.__name__)
