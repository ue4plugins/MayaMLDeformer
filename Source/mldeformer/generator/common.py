# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

import os
import sys
import logging
import traceback

from . import state
from .util import which
from PySide2 import QtCore

DIRNAME = os.path.dirname(__file__)

self = sys.modules[__name__]
self._activated = False

log = logging.getLogger(__name__)
Modules = state["registeredModules"]


class Module(QtCore.QObject):
    """A piece of the app

    Arguments:
        installer (func): Called during activation
        uninstaller (func): Called  during deactivation
        label (str, optional): Nice name of module
        enabled (bool, optional): Whether or not this module is active
        dependencies (list, optional): List of modules needed in order
            for this module to work.
        after_activated (func, optional): Called after activation,
            takes no arguments
        after_deactivated (func, optional): Called after deactivation,
            takes no arguments

    """

    activated = QtCore.Signal(object, bool)  # (Module, state)

    def __str__(self):
        return self._name

    def __init__(self,
                 installer,
                 uninstaller,
                 label=None,
                 enabled=True,
                 manual=False,
                 dependencies=None,
                 help="",
                 runlevel=0,
                 after_activated=lambda: None,
                 after_deactivated=lambda: None,
                 parent=None,
                 ):

        super(Module, self).__init__(parent)

        self._name = None  # filled in by :func:`register`
        self._label = label
        self._manual = manual
        self._installer = installer
        self._uninstaller = uninstaller
        self._dependencies = dependencies
        self._enabled = enabled
        self._runlevel = runlevel
        self._help = help

        # Edited at run-time
        self._active = False
        self._output = None
        self._error = None

        self._callbacks = {
            "afterActivation": after_activated,
            "afterDeactivation": after_deactivated,
        }

    @property
    def name(self):
        return self._name

    @property
    def manual(self):
        return self._manual

    @manual.setter
    def manual(self, value):
        self._manual = value

    @property
    def label(self):
        """Pretty-printed name of module"""
        return self._label

    @property
    def enabled(self):
        """Can this be activated?"""
        return self._enabled

    @enabled.setter
    def enabled(self, state):
        self._enabled = state

    @property
    def active(self):
        """Has the module been installed?"""
        return self._active

    @active.setter
    def active(self, state):
        self.activate() if state else self.deactivate()

    @property
    def runlevel(self):
        """This modules runrunlevel"""
        return self._runlevel

    @property
    def help(self):
        return self._help

    @property
    def output(self):
        """Return the output of installing"""
        return self._output

    @property
    def failed(self):
        return self._error is not None

    def activate(self, dependencies=True, retry=False):
        if dependencies:
            self._check_dependencies()
            for dep in self._dependencies or []:
                dep = Modules[dep]

                if not dep.active:
                    dep.activate()

        if self.failed and not retry:
            return

        if self.active:
            return

        log.info("Activating module \"%s\"" % self)
        if self._do(*self._installer):
            self._callbacks["afterActivation"]()
            self._active = True
            self.activated.emit(self, True)

        # Once activated, it'll stick with the pack
        self.manual = False

    def deactivate(self, dependencies=True):
        if not self.active:
            return

        log.info("Deactivating module \"%s\".." % self)

        if dependencies:
            self._check_dependencies()
            for dep in self._dependencies or []:
                dep = Modules[dep]

                if not dep._dependencies:
                    continue

                if not dep.active:
                    log.debug("%s wasn't active" % dep)
                    continue

                # Is any module dependent on this module?
                if self.name in dep._dependencies:
                    log.debug(
                        "%s was dependent on %s, deactivating.."
                        % (dep, self)
                    )
                    dep.deactivate()

        if self._do(*self._uninstaller):
            self._callbacks["afterDeactivation"]()
            self._active = False
            self.activated.emit(self, False)

    def _do(self, func, args, kwargs):
        skip = False

        for dep in self._dependencies or []:
            if Modules[dep].failed:
                log.warning("Failed dependency: \"%s\"" % dep)
                skip = True

        if skip:
            return log.warning("\"%s\" skipped, see log for details" % dep)

        try:
            # This can never fail, as it may distrupt
            # subsequent modules from activating/deactivating
            self._output = func(*args, **kwargs)

        except Exception:
            self._error = traceback.format_exc()
            log.debug(self._error)
            log.warning("Module '%s' failed" % self._name)

        else:
            return True

    def _check_dependencies(self):
        """All referenced dependencies must already have been registered"""
        assert all(mod in Modules for mod in self._dependencies or []), (
            "'%s' could not be found" % ", ".join(
            mod for mod in Modules
            if mod not in self._dependencies
        )
        )


def activate(name=None, runlevel=5):
    """Activate all  modules

    Arguments:
        name (str, optional): Activate this registered module.
            If left empty, activate *all* registered modules.
        runlevel (int, optional): Activate up-till this level,
            defaults to 4

    """

    log.info("Activating to runlevel %d" % runlevel)

    modules = [Modules[name]] if name else Modules.values()

    # NOTE: Activate in the order they were registered.
    # The inner "dependencies" will ensure no module
    # is installed unless it's dependent module is
    # installed first.
    for mod in modules:

        # These are activated by hand
        if mod.manual:
            continue

        if mod.runlevel <= runlevel:
            mod.activate()

    if name is None:
        self._activated = True


def deactivate(name=None):
    """De-activate modules"""
    modules = reversed([Modules[name]] if name else Modules.values())

    # IMPORTANT: Deactivate in the reverse order
    for mod in modules:

        # Whether it's manual or not, it needs to go
        if mod.manual:
            pass

        mod.deactivate()


def activated():
    return all(mod.active or mod.manual for mod in Modules.values())


def register(name, module):
    """Register a new  module"""
    Modules[name] = module

    module._name = name
    if not module.label:
        module._label = name

    return module


def module(name):
    return Modules[name]


def modules():
    return list(state["registeredModules"].values())


def install(exe=None):
    pass


def uninstall():
    pass
