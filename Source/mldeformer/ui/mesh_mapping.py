# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

# Maps a base mesh with a target mesh.
# This way we know what is the linear skinned mesh (the base mesh), and which is 
# the target complex deformed mesh (the target mesh).
# We need this information during training, as we need to calculate the mesh deltas between these meshes.
class MeshMapping:
    def __init__(self, base_mesh_name, target_mesh_name, enabled=True):
        self.base_mesh_name = base_mesh_name
        self.target_mesh_name = target_mesh_name
        self.is_enabled = enabled
