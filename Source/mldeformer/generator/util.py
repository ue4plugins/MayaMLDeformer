# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

import os
import re
import sys
import time
import shutil
import logging
import tempfile
import contextlib
from functools import wraps

# Detect OS
WINDOWS = 1
UNIX = 2
UNKNOWN = 3
OS = (
    UNIX if os.name == "posix"
    else WINDOWS if os.name == "nt"
    else UNKNOWN
)

# On Unix, `clock` captures 10ms increments, and `time` to 1ns
# On Windows, `clock` is more sensitive
Timer = time.clock if OS == UNIX else time.time

log = logging.getLogger(__name__)
DoNothing = None

resource_root = os.path.dirname(__file__)
resource_root = os.path.join(resource_root, "res")


def resource(*path):
    """Return path to asset, relative the install directory

    Usage:
        >>> path = resource("dir", "to", "asset.png")
        >>> path == os.path.join(resource_root, "dir", "to", "asset.png")
        True

    Arguments:
        path (str): One or more paths, to be concatenated

    """

    return os.path.join(resource_root, *path)


def which(program):
    """Locate `program` in PATH

    Arguments:
        program (str): Name of program, e.g. "python"

    """

    def is_exe(fpath):
        if os.path.isfile(fpath) and os.access(fpath, os.X_OK):
            return True
        return False

    for path in os.environ["PATH"].split(os.pathsep):
        for ext in os.getenv("PATHEXT", "").split(os.pathsep):
            fname = program + ext.lower()
            abspath = os.path.join(path.strip('"'), fname)

            if is_exe(abspath):
                return abspath

    return None


@contextlib.contextmanager
def tempdir():
    tmp = tempfile.mkdtemp()

    try:
        yield tmp
    finally:
        shutil.rmtree(tmp)


@contextlib.contextmanager
def pythonpath(path):
    sys.path.insert(0, path)
    try:
        yield
    finally:
        sys.path.pop(0)


# Alias
sys_path = pythonpath


def mixedcase_to_title(name):
    """Convert mixedCase to Title Case

    Example:
        >>> mixedcase_to_title("mixedCase")
        'Mixed Case'
        >>> mixedcase_to_title("advancedAttributeName")
        'Advanced Attribute Name'

    """

    return re.sub("([a-z])([A-Z])", "\g<1> \g<2>", name).title()
