"""Commit to Maya's internal Undo queue"""

import os
import sys
import types

from maya import cmds
from maya.api import OpenMaya as om

__version__ = "0.1.0"


def maya_useNewAPI():
    pass


name = "apiundoShared"
if name not in sys.modules:
    sys.modules[name] = types.ModuleType(name)

shared = sys.modules[name]
shared.undo = None
shared.redo = None


def commit(undo, redo=lambda: None):
    """Commit `undo` and `redo` to history

    Arguments:
        undo (func): Call this function on next undo
        redo (func, optional): Like `undo`, for for redo

    """

    if not hasattr(cmds, "apiUndo"):
        install()

    shared.undo = undo
    shared.redo = redo

    # Let Maya know that something is undoable
    cmds.apiUndo()


def install():
    """Load this module as a plug-in

    Call this prior to using the module

    """

    cmds.loadPlugin(__file__, quiet=True)
    shared.installed = True


def uninstall():
    cmds.unloadPlugin(os.path.basename(__file__))
    shared.installed = False


def reinstall():
    """Automatically reload both Maya plug-in and Python module

    FOR DEVELOPERS

    Call this when changes have been made to this module.

    """

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
        self.undo = shared.undo
        self.redo = shared.redo

    def undoIt(self):
        self.displayInfo("Undoing..")
        self.undo()

    def redoIt(self):
        self.displayInfo("Redoing..")
        self.redo()

    def isUndoable(self):
        # Without this, the above undoIt and redoIt will not be called
        return True


def initializePlugin(plugin):
    shared.plugin = plugin
    om.MFnPlugin(plugin).registerCommand(
        apiUndo.__name__,
        apiUndo
    )


def uninitializePlugin(plugin):
    om.MFnPlugin(plugin).deregisterCommand(apiUndo.__name__)
