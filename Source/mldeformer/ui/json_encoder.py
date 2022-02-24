# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

import json


# JSON encoder for some specific objects.
class JsonEncoder(json.JSONEncoder):
    def default(self, object):
        from .attribute_minmax import AttributeMinMax
        from .config import Config
        from .global_settings import GlobalSettings
        from .mesh_mapping import MeshMapping
        from .parameter import Parameter

        if isinstance(object, Config) \
            or isinstance(object, GlobalSettings) \
            or isinstance(object, Parameter) \
            or isinstance(object, AttributeMinMax) \
            or isinstance(object, MeshMapping):
            return object.__dict__
        else:
            return json.JSONEncoder.default(self, object)
