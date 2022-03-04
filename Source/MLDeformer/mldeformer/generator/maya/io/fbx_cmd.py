# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved
"""
Set obj exporter presets.
"""

from maya import cmds

if not cmds.pluginInfo('fbxmaya', q=True, loaded=True):
    cmds.loadPlugin('fbxmaya')


def select_listed_meshes(mesh_list):
    shapes_list = cmds.ls(selection=False, long=True, objectsOnly=True, geometry=True, type='mesh')
    meshes_to_remove = set() 
    if shapes_list:
        all_meshes = cmds.listRelatives(shapes_list, parent=True)
        meshes_to_remove = set(all_meshes) - set(mesh_list) # Remove duplicates and sort by name
    
    all_objects = cmds.ls()
    objects_to_select = list(set(all_objects) - meshes_to_remove)
    cmds.select(objects_to_select)
    
    
def fbx_export(filepath, selected_meshes=[], start_frame=0, end_frame=100):
    '''
    Exports selected objects
    '''

    cmds.FBXResetExport()

    # Mesh
    cmds.FBXExportTriangulate('-v', False)  # ?
    cmds.FBXExportSmoothingGroups('-v', True)
    cmds.FBXExportHardEdges('-v', False)
    cmds.FBXExportTangents('-v', True)
    cmds.FBXExportSmoothMesh('-v', True)
    cmds.FBXExportSkeletonDefinitions('-v', False) #True;False

    # Animation
    cmds.FBXExportBakeResampleAnimation('-v', False)
    cmds.FBXExportAnimationOnly('-v', False)
    cmds.FBXExportBakeComplexAnimation('-v', True)
    cmds.FBXExportBakeComplexStart('-v', start_frame)
    cmds.FBXExportBakeComplexEnd('-v', end_frame)
    cmds.FBXExportBakeComplexStep('-v', 1)
    cmds.FBXExportQuaternion('-v', 'quaternion')  # quaternion|euler|resample
    cmds.FBXExportApplyConstantKeyReducer('-v', False)


    # Objects    
    cmds.FBXExportSkins('-v', True)
    cmds.FBXExportShapes('-v', False)
    cmds.FBXExportInputConnections('-v', False)
    cmds.FBXExportConstraints('-v', False)
    cmds.FBXExportCameras('-v', False)
    cmds.FBXExportLights('-v', False)
    cmds.FBXExportEmbeddedTextures('-v', False)

    # Scene
    cmds.FBXExportReferencedAssetsContent('-v', True)
    cmds.FBXExportInstances('-v', False)
    cmds.FBXExportCacheFile('-v', False)
    cmds.FBXExportAxisConversionMethod('none')
    cmds.FBXExportGenerateLog('-v', False)
    cmds.FBXExportUseSceneName('-v', False)
    cmds.FBXExportInAscii('-v', False)
    cmds.FBXExportFileVersion('-v', 'FBX201800')
    cmds.FBXExportUpAxis('y')
    cmds.FBXExportConvertUnitString('cm')#string [mm|dm|cm|m|km|In|ft|yd|mi]
    cmds.FBXExportScaleFactor(1.0) #float

    old_selection = cmds.ls(selection=True)
    
    select_listed_meshes(selected_meshes)
    
    retval = cmds.FBXExport('-es', '-f', filepath)
    cmds.select(old_selection)
    return retval