"""Commit to Maya's internal Undo queue"""

import os
import sys

from maya import cmds
from maya.api import OpenMaya as om


def maya_useNewAPI():
    pass


# This module is both a Python module and Maya plug-in. Maya doesn't
# play by the rules when it comes to loading modules, so we can't either.
#
# To Maya the __name__ of this module is "__builtin__", therefore in order
# to reference it, we must spell it out by name.
#
# This member is what we use to share data between Python and Maya plug-in.
shared = sys.modules["apiundo"]
shared.undoHistory = list()
shared.redoHistory = list()
shared.installed = False


def commit(undo, redo=lambda: None):
    """Commit `undo` and `redo` to history

    Arguments:
        undo (func): Call this function on next undo
        redo (func, optional): Like `undo`, for for redo

    """

    if not shared.installed:
        install()

    shared.undoHistory.append(undo)
    shared.redoHistory.append(redo)

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
    om.MFnPlugin(plugin).registerCommand(
        apiUndo.__name__,
        apiUndo
    )


def uninitializePlugin(plugin):
    om.MFnPlugin(plugin).deregisterCommand(apiUndo.__name__)
