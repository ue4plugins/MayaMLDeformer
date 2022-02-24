# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

from PySide2 import QtCore
from maya import cmds

from ...maya_event_handler import MayaEventHandler
from ....qtgui.main_window import DeformerMainWindow

# Module level state
self = type("self", (object,), {})
self.timers = list()
self.menu = None
self.installed = False
self.menu_items = {}


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
        Item("Data Generator", show_deformer_ui)

    uninstall_menu()

    # Give modules a chance to finish installing,
    # such that .activated() is correct
    _defer(deferred)


def show_deformer_ui():
    event_handler = MayaEventHandler()
    deformer_ui = DeformerMainWindow(event_handler)
    deformer_ui.show()
    pass


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
