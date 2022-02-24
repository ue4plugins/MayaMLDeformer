# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

from maya import cmds
    
if not cmds.pluginInfo('AbcExport', q=True, loaded=True):
    cmds.loadPlugin('AbcExport')

# --------------------------------------------------------------------------------------------------

def abc_export(filepath,
               # Mesh
               roots=[], no_normals=False, format='ogawa',
               # Animation
               take_start_frame=0, take_end_frame=0, step=1,
               # Scene
               uv_write=True, write_visibility=False, world_space=True,
               # Misc
               verbose=False):
    '''
    Exports selected objects
    '''

    # Set export options.
    command = ''
    command += '-frameRange {} {} '.format(take_start_frame, take_end_frame)
    command += '-step {} '.format(step)
    command += '-dataFormat {} '.format(format)
    if uv_write:
        command += '-uvWrite '
    if write_visibility:
        command += '-writeVisibility '
    if world_space:
        command += '-worldSpace '
    if no_normals:
        command += '-noNormals '
    if verbose:
        command += '-verbose '
    for root in roots:
        command += '-root {} '.format(root)
    command += '-file {}'.format(filepath)
    # Execute command.
    return cmds.AbcExport(j=command)
