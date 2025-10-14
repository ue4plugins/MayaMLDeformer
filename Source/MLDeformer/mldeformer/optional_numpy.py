# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

try:
    import numpy

    __numpy_imported = True
except:
    __numpy_imported = False


def numpy_supported() -> bool:
    return __numpy_imported
