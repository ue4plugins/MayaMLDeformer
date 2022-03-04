# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

from . import api 


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



