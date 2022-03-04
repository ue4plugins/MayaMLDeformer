# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

# The minimum and maximum values of a given attribute.
# This allows us to default given attribute min max values to specific values.
# For example the rotation values could go from -90 to +90 degrees on default.
# These values are ignored when the DCC has already setup a min and max, or when we are dealing with
# a joint and that joint has limits setup.
class AttributeMinMax:
    def __init__(self, name='', min_value=0.0, max_value=1.0):
        self.name = name
        self.min_value = min_value
        self.max_value = max_value
