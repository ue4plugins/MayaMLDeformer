# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved
"""
This module performs certain operations on the character rig.
"""

import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya

from mldeformer.generator.utils.misc import math

try:
    from itertools import izip
except ImportError:  #python3.x
    izip = zip
    
def get_valid_attributes(controller_name, attr_type='translate*', max_num_attr=2):
    """"Get number of valid attributes of a controller.
    Parameters:
        controller_name (str) --  Controller name
        attr_type (str)       --  Attribute type
        max_num_attr (int)    --  Maximum number of allowed controller attributes
    Return:
        Valid attributes for a given controller (ndarray)
    """
    # the attribute should be available.
    attr_list = cmds.listAttr(controller_name, u=True, s=True, k=True, c=False, st=attr_type)
    num_attr = len(attr_list)
    if num_attr > 0 and num_attr <= max_num_attr:
        return attr_list
    return []


def get_valid_controller_attributes(controller_list, attr_type='translate*', max_num_attr=2):
    """"Get total number of valid attributes from a controller list.
    Parameters:
        controller_list (list(str)) -- List of controllers, i.e., selected
                                       transformer nodes in maya.
        attr_type (str)             -- Attribute type.
        max_num_attr (int)          -- Maximum number of allowed controller attributes.
    Return:
        Total number of valid attributes for a given controller
    """
    ctrl_attr_list = []
    for controller_name in controller_list:
        attr_list = get_valid_attributes(controller_name, attr_type, max_num_attr)
        for attr in attr_list:
            ctrl_attr_list.append('{}.{}'.format(controller_name, attr))
    return ctrl_attr_list


def find_valid_controllers(controller_list,
                           target_controller_types=None,
                           tabu_controller_types=None):
    """"Find valid controllers (transformers) in the scene.
    Parameters:
        controller_list (list(str))         --  List of transformers nodes in maya
        target_controller_types (list(str)) --  List of target controller type (keywords only)
        tabu_controller_types (list(str))   --  List of excluded controller (keywords only)
    Return:
        Filtered list of controllers
    """
    target_controllers = []
    for controller_name in controller_list:
        if not target_controller_types or next(
            (type for type in target_controller_types if type in controller_name), None):
            if not tabu_controller_types or not next(
                (type for type in tabu_controller_types if type in controller_name), None):
                target_controllers.append(controller_name)
    return target_controllers


def get_normalized_controller_attributes(controller_attr_list):
    """"Get normalized controller attribute values,
        i.e. rotation and translation with baked joint orient.
    Parameters:
        controller_attr_list (list(str))     --  List of controller attributes that will be fetched.
    Return:
        Normalized controller attribute list
    """
    norm_ctrl_attr_list = []
    for attr in controller_attr_list:
        attr_name, attr_type = attr.split('.')
        # Get xform
        xform = cmds.xform(attr_name, q=True, matrix=True)
        # Transform xform into a MTransformationMatrix object
        transform_mat = OpenMaya.MTransformationMatrix(OpenMaya.MMatrix(xform))
        if 'rotate' in attr_type:
            rot = transform_mat.rotation()
            if 'X' in attr_type:
                norm_ctrl_attr_list.append(math.clamp_angle(math.rads2degs(rot.x)))
            elif 'Y' in attr_type:
                norm_ctrl_attr_list.append(math.clamp_angle(math.rads2degs(rot.y)))
            else:
                norm_ctrl_attr_list.append(math.clamp_angle(math.rads2degs(rot.z)))
        elif 'translate' in attr_type:
            trans = transform_mat.translation()
            if 'X' in attr_type:
                norm_ctrl_attr_list.append(trans.x)
            elif 'Y' in attr_type:
                norm_ctrl_attr_list.append(trans.y)
            else:
                norm_ctrl_attr_list.append(trans.z)
    return norm_ctrl_attr_list


def set_controller_attribute(controller_attr, attr_value):
    """"Set value to controller attribute.
    Parameters:
        controller_attr (str)     --  Controller attribute that will be modified.
        attr_value (float/double) --  Value assigned to the attributes.
    """
    cmds.setAttr(controller_attr, attr_value)


def set_controller_attributes(controller_attr_list, attr_value_list):
    """"Set values to the attribute list.
    Parameters:
        controller_attr_list (list(str))     -- List of controller attributes
                                                that will be modified.
        attr_value_list (list(float/double)) -- List of values assigned to the attributes.
    """
    # The size of both list must be identical.
    if len(controller_attr_list) == len(attr_value_list):
        for attr, val in izip(controller_attr_list, attr_value_list):
            # print(controller_attr_list[i])
            set_controller_attribute(attr, val)
