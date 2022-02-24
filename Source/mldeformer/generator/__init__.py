# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

import collections as _collections

import os

state = {
    # Previous interaction with the file-system is recorded here,
    # for reuse in subsequent calls to a function holding SHIFT
    "history": {},

    # Host plug-ins are recorded for automatic uninstall
    "pluginsLoaded": set(),

    # Reloader modules
    "registeredModules": _collections.OrderedDict(),

    "teardown": [],

}


def unload():
    """Unload every module

    This enables re-import of this package without restarting the
    interpreter, whilst also accounting for import order to avoid/bypass
    cyclical dependencies.

    """

    import sys  # Local import, to prevent leakage

    for key, value in sys.modules.copy().items():
        if key.startswith(__name__):
            sys.modules.pop(key)
