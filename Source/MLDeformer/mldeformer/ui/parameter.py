# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

# A rig parameter.
# This is basically an attribute on an object.
# The parameter has a given minimum and maximum value, as well as a default value.
# The display name is what you see in the table in the UI, while the actual name is the identifier inside the DCC.
class Parameter:
    def __init__(self):
        self.name = ''
        self.display_name = ''
        self.default_value = 0.0
        self.min_value = 0.0
        self.max_value = 1.0
        self.object_type = ''
        self.group_name = ''
