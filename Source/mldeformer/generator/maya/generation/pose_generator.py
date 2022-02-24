# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved
"""
This script generates random poses from a complex and simple rig.
So both rigs must be in the scene.
"""

import maya.cmds as cmds
import random
from ..rig import character_rig
from ..animation.key_frame_animation import KeyFrameAnimation


def random_uniform_list(low, high, size=None):
    if size is None:
        return random.uniform(low, high)
    uniform_list = [random.uniform(low, high) for i in range(size)]
    return uniform_list 


def sample_random_controller_values(target_controller_attributes, target_groups, target_prob, 
                                    max_values=[1],min_values=[0], def_values=[0]):

    """"Sample random controller values with a certain probability in a range defined by user.
    Parameters:
        target_controller_attributes (list (string))    -- Names of controller attributes
        target_groups (dict())   -- {group_name -> [index list]} where the indices ref target_controller_attributes
        target_prob (float)      -- Probability of rejecting a target controller
        max_values (list(float)) -- Maximum allowed value assigned to a controller
        min_values (list(float)) -- Minimum allowed value assigned to a controller
        def_values (list(float)) -- Default value assigned to a controller a.k.a rest value
    Return:
        Vector of random controller values
    """
    num_controllers = len(target_controller_attributes)
    num_groups = len(target_groups)
    
    group_names = list()
    for i in target_groups.keys():
        group_names.append(i)
        
    max_values_size = len(max_values)
    min_values_size = len(min_values)
    def_values_size = len(def_values)
    max_minus_min = [a_i - b_i for a_i, b_i in zip(max_values, min_values)]

    assert max_values_size == min_values_size, 'vector size mismatch len(max_values):{} != len(min_values):{}'.format(
        max_values_size, min_values_size)
    assert def_values_size == max_values_size, 'vector size mismatch len(def_values):{} != len(max_values):{}'.format(
        def_values_size, max_values_size)

    # Perform probability test for selecting controller groups.  Produces a list like [0.341, 0.56, 0.02, 0.49] with 
    # length equal to num_groups
    
    while True:
        prob_test_list = random_uniform_list(0.0, 1.0, num_groups)
        #  Return a boolean list of groups that are going to be sampled
        prob_test_grp = [i < target_prob for i in prob_test_list]
        
        #  Keep resampling until at least one group has a value
        if True in prob_test_grp or num_groups == 0: 
            break
    
    # each group has a list of indices in the controller list. 
    controller_is_default = [True for i in range(num_controllers)]
    for idx, sample_group in enumerate(group_names):
        if prob_test_grp[idx]:
            for control_idx in target_groups[sample_group]:
                controller_is_default[control_idx] = False

    if def_values_size == 1:
        # Create a random vector of controller activations using single user-defined range
        rnd_attr_values = random_uniform_list(min_values[0], max_values[0], num_controllers)
        # Assign default values to controller that do not pass the probability test.
        for i, use_default in enumerate(controller_is_default):
            if use_default:
                rnd_attr_values[i] = def_values[0]
    else:
        assert num_controllers == def_values_size, 'vector size mismatch size:{} != len(def_values):{}'.format(
            num_controllers, def_values_size)
        # Create a random vector of controller activations using multiple user-defined range
        list_prod = [a_i * b_i for a_i, b_i in zip(max_minus_min, random_uniform_list(0.0, 1.0, num_controllers))]
        rnd_attr_values = [a_i + b_i for a_i, b_i in zip(list_prod, min_values)]
        # Assign default values to controller that do not pass the probability test.
        for i, use_default in enumerate(controller_is_default):
            if use_default:
                rnd_attr_values[i] = def_values[i]
    return rnd_attr_values


def generate_samples_from_gui(event_handler, display_time=0.0):
    """ Generate random poses using user-defined parameters from gui
    Params:
        event_handler (MLRigDeformerEventHandler) -- The event handler used to get the config and modify status bar.
        display_time (float)                  -- Time the pose will be displayed
                                                 in maya (default is 0.0)
    Return:
        Whether samples were generated. If not, a message will also be returned.
    """
    deformer_config = event_handler.generator_config

    event_handler.start_progress_bar('Initializing...')
    if event_handler.is_progress_bar_cancelled():
        return False, ''

    # Set random seed
    random.seed(deformer_config.random_seed)
    # Start frame.
    start_frame = deformer_config.start_frame
    # End frame.
    end_frame = start_frame + deformer_config.num_samples
    # Re-adjust timeline before generating keyposes.
    cmds.playbackOptions(minTime=0, maxTime=end_frame)

    # Rig's state attribute.
    rig_state_attr = ''

    # Get all target controller attributes.
    target_controller_attributes = []
    def_attr_values = []
    max_ctrl_attr_values = []
    min_ctrl_attr_values = []
    group_names_dict = {} 
    for paramIndex, param in enumerate(deformer_config.parameters):
        if not event_handler.get_parameter_exists(paramIndex):
            continue
        if param.group_name not in group_names_dict:
            group_names_dict[param.group_name] = []
        group_names_dict[param.group_name].append(paramIndex)
        target_controller_attributes.append(param.display_name)
        def_attr_values.append(param.default_value)
        max_ctrl_attr_values.append(param.max_value)
        min_ctrl_attr_values.append(param.min_value)

    num_controller_attributes = len(target_controller_attributes)
    if num_controller_attributes == 0:
        return False, 'No parameters for sampling poses.'

    # Limit values: Max and min values
    assert len(def_attr_values) == num_controller_attributes, 'attribute value-name size mismatch'

    num_groups = len(group_names_dict)
    
    # Evaluate simple rig with default weights to set mesh at rest pose
    if rig_state_attr:
        cmds.setAttr(rig_state_attr, 0)

    character_rig.set_controller_attributes(target_controller_attributes, def_attr_values)

    event_handler.set_progress_bar_value(20)
    if event_handler.is_progress_bar_cancelled():
        return False, ''

    event_handler.set_progress_bar_value(30)
    if event_handler.is_progress_bar_cancelled():
        return False, ''

    event_handler.set_progress_bar_value(50)
    if event_handler.is_progress_bar_cancelled():
        return False, ''

    event_handler.set_progress_bar_value(100)
    if event_handler.is_progress_bar_cancelled():
        return False, ''

    # Create instance of KeyFrameAnimation
    key_frame_anim = KeyFrameAnimation()
    key_frame_anim.set_controller_attributes(target_controller_attributes)
    event_handler.start_progress_bar('Generating Poses...')

    for i in range(start_frame, end_frame):
        # Create a random vector of controller activations, given a
        # user-defined controller rejection probability.

        rnd_attr_values = sample_random_controller_values(
            target_controller_attributes, group_names_dict, deformer_config.controller_probability,
            max_ctrl_attr_values, min_ctrl_attr_values, def_attr_values)

        # Set keyframe animation.
        key_frame_anim.store_keyframes(i, rnd_attr_values)
        # Update progress bar.
        progress_percentage = int(((i - start_frame) / float(end_frame - start_frame)) * 100.0)
        event_handler.set_progress_bar_value(progress_percentage)

        # User cancelled.
        if event_handler.is_progress_bar_cancelled():
            break

    key_frame_anim.set_all_stored_keyframes()

    return True, ''
