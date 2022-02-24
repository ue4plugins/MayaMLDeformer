# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

import json


class ParameterFilter:
    def __init__(self):
        self.include_children = False
        self.selected_channels_only = False
        self.include_all = False
        self.include_joints = True
        self.include_transforms = True
        self.include_shapes = False
        self.include_custom_types = list()
        self.exclude_custom_types = list()
        self.exclude_attributes = list()

    def to_json(self):
        data = json.dumps(self,
                          default=lambda o: o.__dict__,
                          sort_keys=True,
                          indent=4)
        return data

    def parse_filter_settings_json_data(self, data):
        self.include_children = data['include_children']
        self.selected_channels_only = data['selected_channels_only']
        self.include_all = data['include_all']
        self.include_joints = data['include_joints']
        self.include_transforms = data['include_transforms']
        self.include_shapes = data['include_shapes']

        del self.include_custom_types[:]
        for item in data['include_custom_types']:
            self.include_custom_types.append(item)

        del self.exclude_custom_types[:]
        for item in data['exclude_custom_types']:
            self.exclude_custom_types.append(item)

        del self.exclude_attributes[:]
        for item in data['exclude_attributes']:
            self.exclude_attributes.append(item)
