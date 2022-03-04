# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

import contextlib
import logging
import os
import tempfile

from PySide2 import QtCore
from PySide2 import QtWidgets
from maya import cmds

from . import (
    maya_menu
)

# Module level state
self = type("self", (object,), {})
self.timers = list()
self.menu_items = {}
self.dev_menu = None
self.installed = False
self.controller = None
self.activated = False
# Containers for the GUI
log = logging.getLogger(__name__)

DEVELOPER = bool(
    os.getenv("UE_DEVELOPER") in ["1", "True", "true"])


@contextlib.contextmanager
def empty_scene(preserve=False, reset=True):
    """Context handler for an empty scene

    Arguments:
        preserve (bool, optional): save the scene, re-open it when finished?
            Default is to leave an empty scene.
        reset (bool, optional): If you preserve, should I also
            keep the current selection? Defaults to True

    """

    existing_selection = cmds.ls(selection=True)
    existing_scene = cmds.file(sceneName=True, query=True)
    name, ext = os.path.splitext(existing_scene)

    if preserve:
        # save in a temporary location
        if not existing_scene:
            dirname = tempfile.gettempdir()
            existing_scene = cmds.file(
                rename=os.path.join(dirname, "temp" + ext)
            )

        cmds.file(save=True)

    cmds.file(new=True, force=True)

    try:
        yield
    finally:
        if not existing_scene:
            return

        if not (preserve or reset):
            return

        cmds.file(existing_scene, open=True, force=True)

        if not existing_selection:
            return

        try:
            cmds.select(existing_selection, noExpand=True)
        except RuntimeError:
            # Nodes may no longer exist, which is fine.
            pass


def install(exe=None, auto_activate=True, runlevel=5):
    """Install Reloader into Maya
    """
    if not is_supported_version():
        message = QtWidgets.QMessageBox()
        message.setWindowTitle("Unsupported Version")
        message.setText("This requires Maya 2015 SP3 or higher")
        message.setStandardButtons(message.Ignore | message.Cancel)
        message.setDefaultButton(message.Ignore)

        choice = message.exec_()

        if choice == message.Cancel:
            return

    if auto_activate:
        activate()

    batch_mode = cmds.about(batch=True)

    if not batch_mode:
        if DEVELOPER:
            install_developer_menu()
        maya_menu.install()
        maya_menu.activate()

    log.info("All done")


def is_supported_version():
    # Maya 2015 SP3 or higher
    return cmds.about(apiVersion=True) >= 201505


def Menu(label, parent="MayaWindow"):
    return cmds.menu(
        "ue_" + label,
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


def install_developer_menu():
    def deferred():
        self.dev_menu = Menu("UE_Developer")

        Item("Reinstall", subMenu=True)
        Item("Save Scene", lambda: reinstall(preserve=True))
        Item("Discard Scene Changes", lambda: reinstall(preserve=False))

    uninstall_developer_menu()
    _defer(deferred)


def uninstall_developer_menu():
    if self.dev_menu:
        try:
            cmds.deleteUI(self.dev_menu)
        except RuntimeError:
            # Already deleted
            pass

    self.dev_menu = None


def reinstall(preserve=True):
    # Clear selection to avoid errors after reinstall
    cmds.select(clear=True)

    def before():
        import mldeformer.ui.maya.integration.menu.interactive as interactive
        interactive.install()

    def after():
        from maya import cmds
        cmds.currentTime(previous_time, update=True)

    previous_time = cmds.currentTime(query=True)

    uninstall(preserve, before, after)


def uninstall(preserve=False, during=lambda: None, after=lambda: None):
    def deferred():
        import mldeformer
        import mldeformer.ui.maya.integration.menu.interactive as interactive
        import mldeformer.ui.maya.integration.menu.maya_menu as maya_menu

        with empty_scene(preserve=preserve):
            maya_menu.deactivate()
            maya_menu.uninstall()
            interactive.deactivate()
            mldeformer.unload()
            during()
        after()

    _clear_defer()

    # Give the button a chance to finish being clicked,
    # such that garbage collection can collect it as the
    # above function is running.
    _defer(uninstall_developer_menu, 50)
    _defer(deferred, 100)


def _defer(func, time=100):
    timer = QtCore.QTimer()
    timer.setInterval(time)
    timer.setSingleShot(True)
    timer.timeout.connect(func)
    timer.start()
    self.timers += [timer]


def _clear_defer():
    for timer in self.timers:
        timer.stop()
        timer.deleteLater()

    self.timers[:] = []


def activate():
    maya_menu.activate()
    update_developer_menu()
    self.activated = True


def deactivate():
    _clear_defer()
    uninstall_developer_menu()
    with empty_scene(reset=False):
        maya_menu.deactivate()

    self.activated = False
    update_developer_menu()


def _deferred_set_parent():
    from maya import cmds
    if self:
        cmds.setParent(self.dev_menu, menu=True)


def update_developer_menu():
    # Give Maya a chance to create the menu
    _defer(_deferred_set_parent)
