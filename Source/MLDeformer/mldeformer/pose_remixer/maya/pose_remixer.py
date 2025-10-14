# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as omanim
import math
import mldeformer.optional_numpy

if mldeformer.optional_numpy.numpy_supported():
    import numpy as np


def om_set_keyframes(ctrl_name: str, attr_name: str, key_times: list, key_values: list) -> None:
    """"Set key frames at once using the open maya api
    Parameters:
        ctrl_name   -- Control Name
        attr_name   -- Attribute Name
        key_times   -- The keyframe time values.
        key_values  -- The keyframe values.
    """
    omslist = om.MSelectionList()
    omslist.add("{0}.{1}".format(ctrl_name, attr_name))
    mplug = omslist.getPlug(0)
    mcurve = omanim.MFnAnimCurve(mplug)
    try:
        mcurve.name()  # Errors if the curve does not exist.
    except:
        mcurve.create(mplug)  # If the curve does not exist, create it and attach it to the plug.

    angular_types = [omanim.MFnAnimCurve.kAnimCurveTA, omanim.MFnAnimCurve.kAnimCurveUA]
    if mcurve.animCurveType in angular_types:
        key_values = [math.radians(i) for i in key_values]

    mcurve.addKeys(
        key_times,
        key_values,
        omanim.MFnAnimCurve.kTangentStep,
        omanim.MFnAnimCurve.kTangentStep,
        True)


def has_keyframe_on_every_frame(joint_name: str, start_frame: int, end_frame: int) -> bool:
    # Get all keyframes for the joint's rotation attributes within the specified range.
    for attribute in ['rotateX', 'rotateY', 'rotateZ']:
        keyframes = cmds.keyframe(joint_name, t=(start_frame, end_frame), q=True, at=attribute)

        # Create a set of all frames within the range.
        all_frames = set(range(start_frame, end_frame + 1))
        keyframed_frames = set(keyframes)

        # Check if all frames have keyframes.
        if not all_frames.issubset(keyframed_frames):
            print(f'Joint attribute {joint_name}.{attribute} does not have keys for every frame')
            return False

    return True


def keyframe_every_frame(joint_name: str, start_frame: int, end_frame: int) -> None:
    # Iterate through each frame in the range.
    for attribute in ['rotateX', 'rotateY', 'rotateZ']:
        fixed_frames = False

        # Get the existing keyframes.
        existing_keyframes = cmds.keyframe(joint_name, q=True, tc=True, at=attribute)

        # Now check every frame, and add a keyframe where needed.
        for frame in range(start_frame, end_frame + 1):
            if frame not in existing_keyframes:
                # Get the (interpolated) key value for this frame, and set it.
                rot = cmds.keyframe(joint_name, query=True, eval=True, attribute=attribute, time=(frame,))[0]
                cmds.setKeyframe(joint_name, t=frame, at=attribute, v=rot)
                fixed_frames = True

        if fixed_frames:
            print(f'Keyframes added on some missing frames for {joint_name}.{attribute}')


def remix_poses(joint_groups: list) -> None:
    print('Remixing poses...')

    # Find the list of all joints.
    all_joints = set()
    for joint_list in joint_groups:
        all_joints = all_joints.union(set(joint_list))

    # Find the joint with the lowest last keyframe time, and use that as animation duration. 
    start_frame = 9999999999
    end_frame = -9999999999
    for joint_name in all_joints:
        joint_last_keyframe = cmds.findKeyframe([joint_name], which='last')
        joint_first_keyframe = cmds.findKeyframe([joint_name], which='first')
        end_frame = max(end_frame, joint_last_keyframe)
        start_frame = min(start_frame, joint_first_keyframe)
    start_frame = int(start_frame)
    end_frame = int(end_frame)

    # Make sure each joint has a keyframe on every frame.
    for joint_name in all_joints:
        if not has_keyframe_on_every_frame(joint_name, start_frame, end_frame):
            keyframe_every_frame(joint_name, start_frame, end_frame)
        if not has_keyframe_on_every_frame(joint_name, start_frame, end_frame):
            print('Keyframes not fixed!')

    num_time_values = end_frame - start_frame + 1
    print(f'Animation start frame: {start_frame}')
    print(f'Animation end frame: {end_frame}')

    all_joint_rotations_array = None
    for joint_list in joint_groups:
        for joint_index, joint_name in enumerate(joint_list):
            # Pack the joint rotation keyframes into an array, so we can time-index shuffle them.
            # This gives the rotations in the following format, where RX is rotation X, and F1 is frame 1.
            # So RXF1 means rotation over X-axis on frame 1.
            #
            # RXF0 RYF0 RZF0 RXF1 RYF1 RZF1 RXF2 RYF2 RZF2 ...
            #
            joint_rotations = cmds.keyframe(joint_name, t=(start_frame, end_frame), q=1, at='rotate', vc=1)
            joint_rotations_array = np.array(joint_rotations, dtype=float)

            # Reshape the array so each row is a rotation axis, and each column is a time index.
            # So our array looks like:
            #
            #      Frame0   Frame1    Frame2   Frame3
            # RX: [20,      40,       25,      44    ]
            # RY: [10,      42,       11,      45    ]
            # RZ: [70,      10,       12,      18    ]
            #
            # So index [1, 2] gives Y rotation of Frame2.
            #
            joint_rotations_per_axis = joint_rotations_array.reshape(3, num_time_values)

            # Concatenate this joint's rotation values into one large one that contains rotations for all joints inside this group.
            if joint_index == 0:
                all_joint_rotations_array = np.copy(joint_rotations_per_axis)
            else:
                all_joint_rotations_array = np.concatenate((all_joint_rotations_array, joint_rotations_per_axis), axis=0)

        # Shuffle the transposed array.
        # Shuffle works on rows, not columns, and we want to shuffle by columns, which represent the frames.
        # So this randomizes the frame numbers.
        np.random.shuffle(np.transpose(all_joint_rotations_array))

        # Split the all_rotations array, so we have an array per joint again instead of this big array that contains all joints.
        per_joint_rotations_array = np.split(all_joint_rotations_array, len(joint_list))

        # Build the time array.
        attr_times = om.MTimeArray()
        for frame_index in range(start_frame, end_frame + 1):
            attr_times.append(om.MTime(frame_index, om.MTime.uiUnit()))

        for joint_index, joint_name in enumerate(joint_list):
            for row, attribute in enumerate(['rx', 'ry', 'rz']):
                try:
                    # Delete existing keyframes.
                    cmds.delete(cmds.connectionInfo('{0}.{1}'.format(joint_name, attribute), sfd=1).split('.')[0])
                except:
                    pass

                # Set the new keyframes.
                om_set_keyframes(joint_name, attribute, attr_times, per_joint_rotations_array[joint_index][row, :].tolist())
