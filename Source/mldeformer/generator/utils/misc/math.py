# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved
"""
This module contains simple math functions.
"""

import math


def degs2rads(degs):
    """"Converts degrees into radians.

    Parameters:
        degs (float/double) -- Degrees
    Return:
        Radians
    """
    return degs * math.pi / 180.0


def rads2degs(rads):
    """"Converts radians into degrees.

    Parameters:
        rads (float/double) -- Radians
    Return:
        Degrees
    """
    return rads * 180.0 / math.pi


def clamp_angle(angle, bound=180.0):
    """"Clamps angle in [-bound,bound].

    Parameters:
        degs (float/double)  -- Degrees
        bound (float/double) -- Symmetric boundary, either 180 or 360
    Return:
        Clamped degrees
    """
    if bound == 180.0:
        bound2 = bound * 2
    else:
        bound2 = bound

    while angle < -bound:
        angle = bound2 + angle
    while angle > bound:
        angle = angle - bound2

    return angle
