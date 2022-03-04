# Copyright Epic Games, Inc. All Rights Reserved
import traceback
from maya import cmds
import os

AUTOACTIVATE = not bool(os.getenv("NOAUTOACTIVATE"))
RUNLEVEL = int(os.getenv("RUNLEVEL", 5))

def deferred():
    """Defer installation

    Depends on Maya's GUI having booted up prior to installing
    which is what this little function is responsible for.

    """
    try:
        from mldeformer.ui.maya.integration.menu import interactive
        run_level = RUNLEVEL
        print("Installing generator")
        interactive.install(auto_activate=AUTOACTIVATE, runlevel=run_level)
    except Exception:
        traceback.print_exc()

cmds.evalDeferred(deferred)


