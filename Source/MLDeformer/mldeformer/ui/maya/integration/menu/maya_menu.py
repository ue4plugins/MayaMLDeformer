# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

from maya import cmds

from mldeformer.ui.Qt import QtCore
from mldeformer.ui.maya.maya_event_handler import MayaEventHandler
from mldeformer.ui.qtgui.main_window import DeformerMainWindow
from mldeformer.ui.qtgui.export_window import DeformerExportWindow
from mldeformer.ui.qtgui.pose_extraction_window import PoseExtractionWindow
from mldeformer.ui.qtgui.pose_remixer_window import PoseRemixerWindow

# Module level state
self = type("self", (object,), {})
self.timers = list()
self.menu = None
self.installed = False
self.menu_items = {}
self._deformer_window = None
self._export_window = None
self._pose_extraction_window = None
self._pose_remixer_window = None


def _defer(func, time=100):
    timer = QtCore.QTimer()
    timer.setInterval(time)
    timer.setSingleShot(True)
    timer.timeout.connect(func)
    timer.start()
    self.timers += [timer]


def Menu(label, parent="MayaWindow"):
    return cmds.menu(
        "ws_" + label,
        label=label,
        tearOff=True,
        parent=parent
    )


def Item(label, func=None, **kwargs):
    kwargs["subMenu"] = kwargs.pop("subMenu", False)

    if func:
        # "lambda _" because the menu option passes the index of
        # the visual menu Item, and "=None" to support repeating
        # the menu command by hitting `g`
        kwargs["command"] = lambda _=None: func()

    item = cmds.menuItem(label, **kwargs)
    self.menu_items[label] = item
    return item


def Divider(label=None):
    cmds.menuItem(divider=True, dividerLabel=label)


def install_menu():
    print("Installing UE MLDeformer menu")

    def deferred():
        self.menu = Menu("UE MLDeformer")
        Divider()
        Item("Random Pose Generator", show_deformer_ui)
        Item("Export to Unreal", show_export_ui)
        Item("Pose Extraction", show_pose_extraction_ui)
        Item("Pose Remixer", show_pose_remixer_ui)

    uninstall_menu()

    # Give modules a chance to finish installing,
    # such that .activated() is correct
    _defer(deferred)


def show_pose_extraction_ui():
    if self._pose_extraction_window:
        try:
            self._pose_extraction_window.show()
            return
        except (RuntimeError, AttributeError):
            pass

    event_handler = MayaEventHandler()
    window = PoseExtractionWindow(event_handler)
    window.show()
    self._pose_extraction_window = window


def show_pose_remixer_ui():
    if self._pose_remixer_window:
        try:
            self._pose_remixer_window.show()
            return
        except (RuntimeError, AttributeError):
            pass

    event_handler = MayaEventHandler()
    window = PoseRemixerWindow(event_handler)
    window.show()
    self._pose_remixer_window = window


def show_deformer_ui():
    if self._deformer_window:
        try:
            self._deformer_window.show()
            return
        except (RuntimeError, AttributeError):
            pass

    event_handler = MayaEventHandler()
    window = DeformerMainWindow(event_handler)
    window.show()
    self._deformer_window = window


def show_export_ui():
    if self._export_window:
        try:
            self._export_window.show()
            return
        except (RuntimeError, AttributeError):
            pass

    event_handler = MayaEventHandler()
    window = DeformerExportWindow(event_handler)
    window.show()
    self._export_window = window


def uninstall_menu():
    if self.menu:
        try:
            cmds.deleteUI(self.menu)
        except RuntimeError:
            # Already deleted
            pass
    self.menu = None


def install():
    install_menu()


def uninstall():
    uninstall_menu()


def activate():
    pass


def deactivate():
    pass
