# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

import os
import math
import time
import tempfile
import mldeformer.optional_numpy

# Maya specific imports.
from maya import cmds
from maya.api import OpenMaya
import maya.mel as mel
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as omanim

# Load the FBX Plugin.
if not cmds.pluginInfo('fbxmaya', q=True, loaded=True):
    cmds.loadPlugin('fbxmaya')

if mldeformer.optional_numpy.numpy_supported():
    import numpy as np


class Transform(object):
    def __init__(self, translation: [float], rotation: [float], scale: [float]):
        """The constructor, which takes a translation, rotation and scale.
        
        Args:
            translation -- The translation, as a list of 3 floats. 
            rotation    -- The rotation angles, in radians, as a list of 3 floats.
            scale       -- The scale factor, as a list of 3 floats.
        """
        self.translation = translation
        self.rotation = rotation
        self.scale = scale


class Joint(object):
    def __init__(self, joint_name: str):
        """The constructor.

        Args:
            joint_name -- The name of the joint.
        """
        selection_list = OpenMaya.MSelectionList()
        selection_list.add(joint_name)
        dag_path = selection_list.getDagPath(0)

        self.transform = OpenMaya.MFnTransform(dag_path)
        self.plug_tx = self.transform.findPlug('translateX', False)
        self.plug_ty = self.transform.findPlug('translateY', False)
        self.plug_tz = self.transform.findPlug('translateZ', False)
        self.plug_rx = self.transform.findPlug('rotateX', False)
        self.plug_ry = self.transform.findPlug('rotateY', False)
        self.plug_rz = self.transform.findPlug('rotateZ', False)
        self.plug_ro = self.transform.findPlug('rotateOrder', False)
        self.plug_sx = self.transform.findPlug('scaleX', False)
        self.plug_sy = self.transform.findPlug('scaleY', False)
        self.plug_sz = self.transform.findPlug('scaleZ', False)

    def get_translation(self, context: OpenMaya.MDGContext) -> [float]:
        """Get the translation of this joint, returned as a list of 3 floats.
        
        Args:
            context -- The maya context, which contains the time value.

        Returns:
            A list 3 float values, representing the x, y and z translation.
        """
        tx = self.plug_tx.asMDistance(context).value
        ty = self.plug_ty.asMDistance(context).value
        tz = self.plug_tz.asMDistance(context).value
        return [tx, ty, tz]

    def get_rotation(self, context: OpenMaya.MDGContext) -> [float]:
        """Get the rotation of this joint, returned as a list of 3 floats, in radians.

        Args:
            context -- The maya context, which contains the time value.

        Returns:
            A list 3 float values, representing the x, y and z rotation, in radians.
        """
        rx = self.plug_rx.asMAngle(context).value
        ry = self.plug_ry.asMAngle(context).value
        rz = self.plug_rz.asMAngle(context).value
        ro = self.plug_ro.asShort(context)
        r = OpenMaya.MEulerRotation(rx, ry, rz, ro)
        return [r.x, r.y, r.z]

    def get_scale(self, context: OpenMaya.MDGContext) -> [float]:
        """Get the scale of this joint, returned as a list of 3 floats.

        Args:
            context -- The maya context, which contains the time value.

        Returns:
            A list 3 float values, representing the x, y and z scale factors.
        """
        sx = self.plug_sx.asDouble(context)
        sy = self.plug_sy.asDouble(context)
        sz = self.plug_sz.asDouble(context)
        return [sx, sy, sz]

    def get_transform(self, context: OpenMaya.MDGContext) -> Transform:
        """Get the transformation of this joint at a given time as defined by a Maya context.

        Args:
            context -- The maya context, which contains the time value.

        Returns:
            The Transform object, which contains the translation, rotation (in radians) and scale.
        """
        return Transform(self.get_translation(context), self.get_rotation(context), self.get_scale(context))


class Skeleton(object):
    def __init__(self, joints: [str]):
        """The constructor which builds a list of Joint objects.
        
        Args:
            joints -- The list of joint names that are part of this skeleton.
        """
        self.joints = [Joint(joint) for joint in joints]

    def get_transforms(self, context=None) -> [Transform]:
        """Get the transformations of all joints.
        
        Args:
            context -- The Maya context, which contains the time value to sample the transforms at.

        Returns:
            A list of Transform objects, in the same order as the joints inside the skeleton.
        """
        if context is None:
            context = OpenMaya.MDGContext()

        transforms = [joint.get_transform(context) for joint in self.joints]
        return transforms


def get_fbx_files_from_folder(folder: str) -> [str]:
    """Get a list of all Fbx files inside a specific folder.   
    This essentially scans the folder for all files using the ".fbx" file extension.
    
    Args:
        folder -- The path to the folder to scan for Fbx files.

    Returns:
        A list of strings, where each string represents the absolute path to an Fbx file inside the specified folder.
    """
    fbx_files = list()
    base_names = os.listdir(folder)
    for base_name in base_names:
        name, ext = os.path.splitext(base_name)
        if ext.lower() == '.fbx':
            fbx_file = os.path.abspath(os.path.join(folder, base_name))
            fbx_files.append(fbx_file)

    return fbx_files


def extract_common_joints_from_fbx_files(fbx_files: [str]) -> [str]:
    """Extract a list of joint names that are present in all the Fbx files in a given folder.
    
    Args:
        fbx_files -- The list of fbx file names to inspect.

    Returns:
        A list of joint names that are present inside all the Fbx files.
    """
    final_list = list()
    fbx_joints_list = list()
    for fbx_file in fbx_files:
        print(f'Loading Fbx {fbx_file} to find common joints')
        cmds.file(new=True, force=True)
        cmds.FBXImportSetMayaFrameRate('-v', True)
        cmds.FBXImportSkins('-v', False)  # Skip importing skins.
        cmds.FBXImportShapes('-v', False)  # Skip importing shapes.
        cmds.FBXImportLights('-v', False)  # Skip importing lights.
        cmds.FBXImport('-f', fbx_file)

        joints = cmds.ls(type='joint')
        fbx_joints_list.append(joints)

    # Now fbx_joints_list is a list of lists. Find all common joints
    final_list = list(set.intersection(*[set(subset) for subset in fbx_joints_list]))
    return final_list


def get_frame_poses_from_fbx_files(fbx_files: [str], joints: [str], max_frames_per_fbx: int) -> list:
    """Get a list of frames, where each frame contains a list of transforms, one for each joint.
    This will concatenate all frames from individual Fbx files. So if you have 3 animation Fbx files each 300 frames, it will return
    a list of 900 frames, assuming we do not go over the max_frames_per_fbx limit in each Fbx.
    
    Args:
        fbx_files           -- The list of Fbx files to extract the transforms from.
        joints              -- The list of joints names to load the transform for.
        max_frames_per_fbx  -- The maximum number of frames to load from each individual Fbx file.

    Returns:
        A list of lists of Transform objects. The indexing is the following: returnedValue[frame_index][joint_index] is of type Transform.
    """
    # Extract a pose for each frame from each fbx file in the folder.
    data = list()
    for fbx_file in fbx_files:
        fbx_data = get_frame_poses_from_fbx_file(fbx_file, joints, max_frames_per_fbx)
        data.extend(fbx_data)

    return data


def get_frame_poses_from_fbx_file(fbx_file: str, joints: [str], max_frames_per_fbx: int) -> list:
    """Get a list of frames, where each frame contains a list of transforms, one for each joint.
    
    Args:
        fbx_file            -- The path to the fbx file to load.
        joints              -- The list of joints names to load the transform for.
        max_frames_per_fbx  -- The maximum number of frames to load from this Fbx file.

    Returns:
        A list of lists of Transform objects. The indexing is the following: returnedValue[frame_index][joint_index] is of type Transform.
    """
    print(f'Importing Fbx from file {fbx_file} to read transforms')
    start_time = time.time()
    cmds.file(new=True, force=True)
    cmds.FBXImportSetMayaFrameRate('-v', True)
    cmds.FBXImportSkins('-v', False)  # Skip importing skins.
    cmds.FBXImportShapes('-v', False)  # Skip importing shapes.
    cmds.FBXImportLights('-v', False)  # Skip importing lights.
    cmds.FBXImport('-f', fbx_file)

    # Get the frame range.
    min_frame = int(cmds.playbackOptions(q=True, minTime=True))
    max_frame = int(cmds.playbackOptions(q=True, maxTime=True))

    if max_frames_per_fbx <= 0:
        max_frames_per_fbx = 1000000000

    if max_frame - min_frame >= max_frames_per_fbx:
        max_frame = min_frame + max_frames_per_fbx

    num_frames = max_frame - min_frame + 1
    print(f'Reading {num_frames} frames from Fbx {fbx_file}')
    units = OpenMaya.MTime.uiUnit()

    progress_bar = mel.eval('$tmp = $gMainProgressBar')
    cmds.progressBar(progress_bar,
                     edit=True,
                     beginProgress=True,
                     isInterruptable=True,
                     status='Storing Fbx Frames',
                     maxValue=100)

    # For each frame, grab all joint transforms.
    skeleton = Skeleton(joints)
    transforms = list()
    for i, frame in enumerate(range(min_frame, max_frame + 1)):
        progress = (i / num_frames) * 100
        cmds.progressBar(progress_bar, edit=True, progress=progress)

        # Get transformations at the current frame.
        mtime = OpenMaya.MTime(frame, units)
        context = OpenMaya.MDGContext(mtime)
        transforms.append(skeleton.get_transforms(context))
    print(f'Grabbing transforms from {fbx_file} took {time.time() - start_time:.2f} seconds')

    cmds.progressBar(progress_bar, edit=True, endProgress=True)
    return transforms


def set_keyframes(control_name: str, attribute_name: str, key_times, key_values):
    """Set all keyframes at once using the open maya api for a given attribute on a given control.
    
    Args:
        control_name   -- The name of the control that we set the attribute keys for.
        attribute_name -- The attribute name on the control.
        key_times      -- The time values. Needs to be the same length as key_values.
        key_values     -- The values of the keys. Needs to be the same length as key_times.
    """

    maya_key_times = om.MTimeArray()
    for i in range(len(key_times)):
        maya_key_times.append(om.MTime(key_times[i], om.MTime.uiUnit()))

    selection_list = om.MSelectionList()
    selection_list.add(f'{control_name}.{attribute_name}')
    mplug = selection_list.getPlug(0)
    maya_curve = omanim.MFnAnimCurve(mplug)
    try:
        maya_curve.name()  # Throws an exception if the curve doesn't exist.
    except:
        try:
            maya_curve.create(mplug)  # If the curve does not exist, create it and attach it to the plug.
        except:
            # When we hit this path the attribute cannot be animated, because it is locked or driven.
            print(f'Attribute \'{mplug}\' cannot be animated, skipping...')
            return

    angular_types = [omanim.MFnAnimCurve.kAnimCurveTA, omanim.MFnAnimCurve.kAnimCurveUA]
    if maya_curve.animCurveType in angular_types:
        key_values = [math.radians(i) for i in key_values]

    maya_curve.addKeys(maya_key_times,
                       key_values,
                       omanim.MFnAnimCurve.kTangentStep,
                       omanim.MFnAnimCurve.kTangentStep,
                       False)


def create_animation(frames: [int], common_joints: [str], joint_transforms: list):
    """Create the animation that contains all 'best' frames from the Fbx poses that we read.
    So this will generate the final animation we will see in the Maya viewport/timeline.
    
    Args:
        frames              -- The list of frame numbers we read from the Fbx files. This points inside the joint_transforms list.
        common_joints       -- The list of joint names for the joints that exist inside all Fbx files we imported animation data from. 
        joint_transforms    -- The list of joint transforms. The indexing works like this: joint_transforms[frame_index][joint_index] is a Transform.
    """
    assert (len(joint_transforms[0]) == len(common_joints))
    print(f'Setting {len(frames)} keyframes for {len(common_joints)} joints')
    start_time = time.time()

    progress_bar = mel.eval('$tmp = $gMainProgressBar')
    cmds.progressBar(progress_bar, edit=True, beginProgress=True, isInterruptable=True, status='Setting keyframes', maxValue=100)

    key_times = [i for i in range(len(frames))]

    for j, joint in enumerate(common_joints):
        progress = (j / len(common_joints)) * 100
        cmds.progressBar(progress_bar, edit=True, progress=progress)

        tx_values = list()
        ty_values = list()
        tz_values = list()
        rx_values = list()
        ry_values = list()
        rz_values = list()
        sx_values = list()
        sy_values = list()
        sz_values = list()
        for frame in frames:
            pos = joint_transforms[frame][j].translation
            tx_values.append(pos[0])
            ty_values.append(pos[1])
            tz_values.append(pos[2])

            rot = joint_transforms[frame][j].rotation
            rx_values.append(math.degrees(rot[0]))
            ry_values.append(math.degrees(rot[1]))
            rz_values.append(math.degrees(rot[2]))

            scale = joint_transforms[frame][j].scale
            sx_values.append(scale[0])
            sy_values.append(scale[1])
            sz_values.append(scale[2])

        # Translation keys.
        set_keyframes(control_name=joint, attribute_name='tx', key_times=key_times, key_values=tx_values)
        set_keyframes(control_name=joint, attribute_name='ty', key_times=key_times, key_values=ty_values)
        set_keyframes(control_name=joint, attribute_name='tz', key_times=key_times, key_values=tz_values)

        # Rotation keys.
        set_keyframes(control_name=joint, attribute_name='rx', key_times=key_times, key_values=rx_values)
        set_keyframes(control_name=joint, attribute_name='ry', key_times=key_times, key_values=ry_values)
        set_keyframes(control_name=joint, attribute_name='rz', key_times=key_times, key_values=rz_values)

        # Scale keys.
        set_keyframes(control_name=joint, attribute_name='sx', key_times=key_times, key_values=sx_values)
        set_keyframes(control_name=joint, attribute_name='sy', key_times=key_times, key_values=sy_values)
        set_keyframes(control_name=joint, attribute_name='sz', key_times=key_times, key_values=sz_values)

    cmds.progressBar(progress_bar, edit=True, endProgress=True)
    print(f'Setting keyframes took {time.time() - start_time:.2f} seconds')


def calc_means(data: [om.MFloatArray], subtract_frame: int, out_means: [float]) -> [float]:
    """This inputs a list of float arrays. It will calculate the mean of each float array and output an array of those means.
    So if we input a list of 10 MFloatArrays, we will output a list of 10 floats, where each of these floats represents the mean of those
    float arrays after we subtract the values of a given subtract_frame from it and square that.
    Essentially it calculates the mean of the square errors versus another frame.
    The reason why this function doesn't return a new list is for a slight performance benefit when reusing the same list each iteration.
    
        Example input:
            data = [1, 2, 0]  -->  -[1, 2, 0] = [0, 0, 0] ^ 2 = [0, 0, 0] -> mean = 0  
                   [2, 5, 2]  -->  -[1, 2, 0] = [1, 3, 2] ^ 2 = [1, 9, 4] -> mean = 4.6667
                   [3, 3, 1]  -->  -[1, 2, 0] = [2, 1, 1] ^ 2 = [4, 1, 1] -> mean = 2
                  
            subtract_frame = 0
    
        Output for the above example input (written into out_means):        
            [0, 4.6667, 2]
                    
    Args:
        data            -- The list of Maya float arrays.
        subtract_frame  -- The frame number that indicates which frame we should make the data relative to.
        out_means       -- The output means list, which should already be of the right size (len(data)).
    """
    num_frames = len(data)
    assert (num_frames > 0)
    num_items = len(data[0])

    for frame in range(num_frames):
        # Calculate: mean(data[frame] - data[subtract_frame])
        mean = 0.0
        for i in range(num_items):
            mean += (data[frame][i] - data[subtract_frame][i]) ** 2.0
        if num_items > 0:
            mean /= float(num_items)

        out_means[frame] = mean


def find_max_item_index(data: om.MFloatArray) -> int:
    """Find the item index that has the maximum value.
    
    Args:
        data -- The array of float values we will search the maximum value in.

    Returns:
        The index inside the float array that contains the highest value.
        If multiple items have the same highest value, the first one is returned.
        If no item is found, because the array is empty, -1 is returned.
    """
    highest_index = -1
    highest_value = -1000000000.0
    for i, value in enumerate(data):
        if value > highest_value:
            highest_value = value
            highest_index = i
    return highest_index


def calc_minimum(a: om.MFloatArray, b: om.MFloatArray) -> om.MFloatArray:
    """Output the minimum values of two float arrays of the same length.
    
        Example input:
            a = [1, 4, 5]
            b = [4, 2, 6]
           
        Output for the example: [1, 2, 5]
    
    Args:
        a -- The first array. 
        b -- The second array.

    Returns:
        This returns a new array of floats where each element contains the minimum value of each element.
    """
    num_items = len(a)
    result = om.MFloatArray()
    result.setLength(num_items)
    for i in range(num_items):
        result[i] = min(a[i], b[i])
    return result


def find_output_frames(joint_rotations: [list], num_output_poses: int) -> [int]:
    """Find the 'best' frames based on a list of frames of joint rotation data.
    We use a greedy algorithm which finds the poses with the largest deviation in rotation.
    The number of input frames equals to len(joint_rotations)
    
    Args:
        joint_rotations     -- The list of lists of rotation angles.
                               With indexing like: joint_rotations[frame_index][joint_index*3] followed by x, y, z rotation angles, in radians. 
        num_output_poses    -- The number of poses we wish to output. This must be equal or less than the number of input frames, which
                               is equal to len(joint_rotations). 

    Returns:
        The list of frame numbers that we want to output into an animation.
    """
    print('Finding best frames')
    progress_bar = mel.eval('$tmp = $gMainProgressBar')
    cmds.progressBar(progress_bar, edit=True, beginProgress=True, isInterruptable=True, status='Finding Best Frames', maxValue=100)

    # Find the best 'num_output_poses' number of frames.
    start_time = time.time()

    # Build a flat list with rotation angles for each frame.
    # Indexed like r[frame_index][joint_index*3] to get the 3 rotation angles of a specific joint at a specific frame.
    r = list()
    num_input_frames = len(joint_rotations)
    for frame in range(num_input_frames):
        r.append(om.MFloatArray(joint_rotations[frame]))

    assert (len(r) == num_input_frames)

    frames = [0, ]  # Add the rest pose as first frame.
    if not mldeformer.optional_numpy.numpy_supported():
        # Already pre-create lists of the right size.
        means = [0.0 for i in range(num_input_frames)]
        best_means = [0.0 for i in range(num_input_frames)]
        calc_means(r, 0, means)

        # Do the greedy search.
        num_frames = len(means)
        while len(frames) < num_output_poses and len(frames) < num_input_frames:
            progress = (len(frames) / min(num_output_poses, num_input_frames)) * 100
            cmds.progressBar(progress_bar, edit=True, progress=progress)
            best_frame = find_max_item_index(means)
            calc_means(r, best_frame, best_means)  # Stores output in best_means.
            frames.append(best_frame)
            for frame in range(num_frames):
                means[frame] = min(best_means[frame], means[frame])
    else:  # We have numpy support.
        rotations = np.array(r)
        dist = ((rotations - rotations[0]) ** 2).mean(axis=1)
        while len(frames) < num_output_poses and len(frames) < num_input_frames:
            progress = (len(frames) / min(num_output_poses, num_input_frames)) * 100
            cmds.progressBar(progress_bar, edit=True, progress=progress)
            best_frame = np.argmax(dist).item()
            best_dist = ((rotations - rotations[best_frame]) ** 2).mean(axis=1)
            frames.append(best_frame)
            dist = np.minimum(dist, best_dist)

    cmds.progressBar(progress_bar, edit=True, endProgress=True)
    print(f'Frame search took {time.time() - start_time:.2f} seconds')
    return frames


def create_scene_backup() -> tuple:
    """Create a backup of the current Maya scene.
    This will be saved inside the operating system temp dir.
    
    Returns:
        The path to the backup file, and the path to the current file.
    """
    # Get the current scene's filename and extension.
    existing_scene = os.path.abspath(cmds.file(sceneName=True, query=True))
    print(f'Existing scene: {existing_scene}')
    file_name, file_extension = os.path.splitext(existing_scene)

    # When we deal with an fbx or ascii file, set the file type to ascii.
    # If we don't do this and have an fbx imported, saving will fail.
    file_type = 'mayaBinary'
    if file_extension.lower() == '.fbx' or file_extension.lower() == '.ma':
        file_extension = '.ma'
        file_type = 'mayaAscii'

    # Do a 'save as' to the temp file.
    temp_dir = tempfile.gettempdir()
    renamed_file = os.path.abspath(os.path.join(temp_dir, "pose_extractor_temp" + file_extension))
    temp_scene = os.path.abspath(cmds.file(rename=renamed_file))
    print(f'Saving current scene backup as {temp_scene}')
    cmds.file(save=True, force=True, type=file_type)
    return temp_scene, existing_scene


def restore_scene_backup(temp_scene: str, existing_scene: str):
    """Restore a backup of a specific Maya scene that we created using create_scene_backup().
    This will load the backup scene file and set its current file path to the original path, essentially replacing it with the backup.
    
    Args:
        temp_scene      -- The backup scene's file path.
        existing_scene  -- The original scene's file path.
    """
    print(f'Restoring old scene from {temp_scene}')
    cmds.file(new=True, force=True)
    cmds.file(temp_scene, open=True, force=True)
    if existing_scene:
        print(f'Restoring old scene name to {existing_scene}')
        cmds.file(rename=existing_scene)


def build_joint_list(fbx_files: [str], input_joints: [str]) -> tuple:
    """Build a list of joints that we can operate on.
    This will load all the Fbx files and find the common joints that exist inside all of the Fbx's.
    We also filter that list by an input_joints list and output a list of joint indices.
    
        Example:
            Fbx1.fbx contains [upper_arm, lower_arm, lower_arm_twist, hand]
            Fbx2.fbx contains [clavicle, upper_arm, lower_arm, lower_arm_twist, hand]            

            input_joints = [upper_arm, lower_arm, hand, finger_tip]
            
        Output for example:
            [0, 1, 3],
            [upper_arm, lower_arm, lower_arm_twist, hand]
            
        Note that the finger_tip is removed, as it isn't a common joint inside the Fbx files.
        Also the twist bones are excluded from the returned indices.
        The clavicle exists in only one animation file and not in ALL of them, so it is not included in the returned common bone name list.
        
    Args:
        fbx_files       -- The list of Fbx files to find the common joints in.
        input_joints    -- A list of joints we want to use during our greedy search. This might for example exclude twist joints.

    Returns:
        This returns two items. The first is a list of integers, which represents the indices inside the second returned value.
        The second returned value is the list of strings, which are the joint names that exist in ALL of the Fbx files.
        The first list are the joint indices inside the list of those common joints. The indices are the filtered list of joints that
        we will use in our greedy search.
    """
    # Get a list of joints that all fbx files have in common.
    print('Extracting joint list from Fbx files')
    fbx_joints = extract_common_joints_from_fbx_files(fbx_files=fbx_files)
    print('Joints in all Fbx files:', fbx_joints)

    # Get the list of joints that exist both in all Fbx files and the current Maya scene.     
    all_joints = cmds.ls(type='joint')
    common_joints = list(set(fbx_joints) & set(all_joints))
    print('Common joints:', common_joints)

    # Now build a list of the joints that are both common and are in the list of input joints (picked from the Maya scene).
    final_joint_list = list()
    for joint in input_joints:
        if joint in all_joints:
            if joint in fbx_joints:
                final_joint_list.append(joint)
            else:
                print(f'WARNING: Joint \'{joint}\' cannot be found inside ALL input Fbx files, ignoring this joint.')

    print('Input joints in Maya but not in Fbx:', list(set(input_joints) - set(final_joint_list)))
    print('Joint list used during pose search:', final_joint_list)

    common_joints_indices = list()
    for joint in final_joint_list:
        common_joints_indices.append(common_joints.index(joint))

    return common_joints_indices, common_joints


def insert_rest_pose_as_first_frame(common_joint_transforms: [list], common_joints: [str], selected_ids: [int],
                                    selected_joint_rotations: [list]) -> tuple:
    """Insert the rest pose inside the list of all already sampled poses.    
    
    Args:
        common_joint_transforms     -- The list of all common joint transforms for all frames.
                                       Indexed as common_joint_transforms[frame_index][joint_index] is a Transform.
        common_joints               -- The list of common bone names, which are bones that exist in ALL Fbx files.
        selected_ids                -- The indices inside the common_joints array of joints we want to include in the greedy pose search later on.
        selected_joint_rotations    -- The joint rotations for the selected joints. 
                                       Indexed as selected_joint_rotations[frame_index][joint_index*3] which is followed by x, y, z rotation angles
                                       in radians.

    Returns:
        This returns two values, from which the first is the list of all joint transforms, now with the rest pose on frame 0.
        The second value is a list of all joint rotations for the selected bones as specified by the selected_ids list.
        The indexing of the returned values works the same as described in the parameter docs above.
    """
    rest_skeleton = Skeleton(common_joints)
    rest_all_joints_transforms = rest_skeleton.get_transforms()
    assert (len(rest_all_joints_transforms) == len(common_joints))

    rest_selected_joints_rotations = list()
    for joint_index in selected_ids:
        rest_selected_joints_rotations.extend(rest_all_joints_transforms[joint_index].rotation)

    # Insert rest pose at frame 0.
    common_joint_transforms.insert(0, rest_all_joints_transforms)
    selected_joint_rotations.insert(0, rest_selected_joints_rotations)

    return common_joint_transforms, selected_joint_rotations


def load_fbx_animation_transforms(fbx_files: [str],
                                  common_joints: [str],
                                  selected_ids: [int],
                                  max_frames_per_fbx: int = 100000000) -> tuple:
    """Load all joint transforms from a specific list of Fbx files.
    This will basically load all frames and store a skeleton pose for each frame by storing the transforms of each of the common joints.
    With common joints we mean the list of joints that are present in ALL Fbx files.
    
    Args:
        fbx_files           -- The list of fbx file paths. 
        common_joints       -- The list of joint names that exist in all the Fbx files.
        selected_ids        -- The list of index values inside the common_joints list for all the joints that we want to include in the greedy search
                               later on.
        max_frames_per_fbx  -- The maximum number of frames to import per Fbx files.

    Returns:
        This returns two values.
        The first is the list of joint transforms for all the common joints. This is indexed as follows:
        common_joint_transforms[frame_index][joint_index] is a Transform.
        The second returned value is the list of rotation angles for each selected joint, and is indexed the following way:
        selected_joint_rotations[frame_index][joint_index*3] is followed by 3 floats, which are the x, y, z rotation angles, in radians.
    """
    print('Loading Fbx animation frames')
    common_joint_transforms = get_frame_poses_from_fbx_files(fbx_files=fbx_files, joints=common_joints, max_frames_per_fbx=max_frames_per_fbx)

    num_frames = len(common_joint_transforms)
    print(f'Total frames loaded: {num_frames}')

    # For each frame, store a list of concatenated joint rotation values.
    selected_joint_rotations = list()
    for frame in range(num_frames):
        rotations = list()
        for joint_index in selected_ids:
            rotations.extend(common_joint_transforms[frame][joint_index].rotation)
        selected_joint_rotations.append(rotations)

    return common_joint_transforms, selected_joint_rotations


def extract_poses(fbx_input_folder: str,
                  joints_to_include_in_search: [str],
                  num_output_poses: int,
                  max_frames_per_fbx: int = 10000000):
    """This is the main function that loads the animation data from the Fbx files and finds the num_output_poses number of best frames using a 
    specific set of joints in a greedy search. It then generates a new animation that is applied to the current Maya scene.
    
    Args:
        fbx_input_folder            -- The folder path to scan for Fbx files and extract their animation data from. 
        joints_to_include_in_search -- The list of joint names that should be used in the search for best poses.                                       
        num_output_poses            -- The number of output poses (frames) to generate in our output animation.
        max_frames_per_fbx          -- The maximum number of frames to load per individual Fbx file. 
    """
    total_start_time = time.time()

    print('Numpy supported:', mldeformer.optional_numpy.numpy_supported())

    # Get the existing file, and save it into a temp file.
    # The returned strings are file names of the current (existing) scene and the temp backup file.
    temp_scene, existing_scene = create_scene_backup()

    # Get a list of all the Fbx files we're interested in.
    # We do this by grabbing all Fbx files inside the specified folder.
    fbx_files = get_fbx_files_from_folder(folder=fbx_input_folder)

    # Get the list of joints we want to use for our pose search.
    # These are valid joints that exist in all Fbx files, and the Maya scene, and inside the input joint list.
    # The returned common_joints contains the list of joint names that exist in all Fbx files and in the Maya scene.
    # The returned selected_ids is a list of indices inside the common_joints list and are the final joints included inside our pose search.
    selected_ids, common_joints = build_joint_list(fbx_files=fbx_files, input_joints=joints_to_include_in_search)

    # Load all animation frames of all Fbx files.
    # This essentially is a buffer with poses that consist of transforms for loaded frames.
    common_joint_transforms, selected_joint_rotations = load_fbx_animation_transforms(
        fbx_files=fbx_files,
        common_joints=common_joints,
        selected_ids=selected_ids,
        max_frames_per_fbx=max_frames_per_fbx)

    # Restore the original scene again using the temp backup file from before.
    # And after we loaded the backup, rename it to the original scene name again.
    restore_scene_backup(temp_scene=temp_scene, existing_scene=existing_scene)

    # Insert the rest pose as first frame to the transform and rotation buffers.
    common_joint_transforms, selected_joint_rotations = insert_rest_pose_as_first_frame(
        common_joint_transforms=common_joint_transforms,
        common_joints=common_joints,
        selected_ids=selected_ids,
        selected_joint_rotations=selected_joint_rotations)

    # Perform the greedy search for the best frame indices.
    frames = find_output_frames(joint_rotations=selected_joint_rotations, num_output_poses=num_output_poses)

    # Set the timeline range.
    cmds.playbackOptions(min=0, max=len(frames) - 1, animationStartTime=0, animationEndTime=len(frames) - 1)

    # Create the animation by adding all keyframes.
    create_animation(frames=frames, common_joints=common_joints, joint_transforms=common_joint_transforms)

    print(f'Pose extraction completed in {time.time() - total_start_time:.2f} seconds!')
