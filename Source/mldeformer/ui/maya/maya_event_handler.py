import traceback

import maya.OpenMayaUI as mui
import maya.cmds as cmds
import maya.mel as mel
from shiboken2 import wrapInstance

from PySide2 import QtWidgets

from mldeformer.ui.event_handler import EventHandler
from mldeformer.ui.attribute_minmax import AttributeMinMax
from mldeformer.ui.parameter import Parameter
from mldeformer.ui.maya.joint_limit import JointLimit

from mldeformer.generator.maya.io.fbx_cmd import fbx_export
from mldeformer.generator.maya.io.abc_cmd import abc_export

try:
    import builtins
except ImportError:
    import __builtin__ as builtins
    
def find_top_joint(node):
    """Return the top joints of a given node.
    >>> find_top_joints('spine_03')
    """
    top_joint = None

    parents = cmds.listRelatives(node, parent=True, type='joint', fullPath=True)
    # Node is already the top joint.
    if not parents:
        top_joint = node
    else:
        parent_joint = None
        while parents:
            parent_joint = parents[0]
            parents = cmds.listRelatives(parent_joint, parent=True, type='joint', fullPath=True)
        if parent_joint:
            # Get short-path.
            top_joint = cmds.ls(parent_joint)[0]
    return top_joint

class MayaEventHandler(EventHandler):
    def __init__(self):
        super(MayaEventHandler, self).__init__()
        self.main_progress_bar = None

    def get_parent_window(self):
        return wrapInstance(builtins.int(mui.MQtUtil.mainWindow()), QtWidgets.QWidget)

    # Get the DCC name, for example 'Maya' or 'Blender'.
    def get_dcc_name(self):
        return 'Maya'

    # Register default min and max setups.
    def register_default_min_max_setup(self):
        self.attribute_min_max_values.append(AttributeMinMax('rotateX', -90.0, 90.0))
        self.attribute_min_max_values.append(AttributeMinMax('rotateY', -90.0, 90.0))
        self.attribute_min_max_values.append(AttributeMinMax('rotateZ', -90.0, 90.0))

    # Register the default filter settings. Modify the filter member in here. You can overload this function.
    def register_default_filter_settings(self, filter):
        filter.exclude_attributes = [
            'visibility',
            'dropoff',
            'smoothness',
            'scaleX',
            'scaleY',
            'scaleZ']

    # Start a new progress bar session.
    def start_progress_bar(self, status_text='Processing...', interruptable=True):
        if self.main_progress_bar:
            self.stop_progress_bar()

        self.main_progress_bar = mel.eval('$tmp = $gMainProgressBar')

        cmds.progressBar(
            self.main_progress_bar,
            edit=True,
            beginProgress=True,
            isInterruptable=interruptable,
            status=status_text,
            maxValue=100)

    # Set the progress bar status message and progress percentage.
    def set_progress_bar_value(self, progress_percentage):
        cmds.progressBar(self.main_progress_bar, edit=True, progress=progress_percentage)

    # Does the user want to cancel progress?
    def is_progress_bar_cancelled(self):
        if self.main_progress_bar:
            exists = cmds.progressBar(self.main_progress_bar, query=True, exists=True)
            if exists:
                result = cmds.progressBar(self.main_progress_bar, query=True, isCancelled=True)
                return result
        return False

    # Stop the progress bar session.
    def stop_progress_bar(self):
        if self.main_progress_bar:
            cmds.progressBar(self.main_progress_bar, edit=True, endProgress=True)
        self.main_progress_bar = None

        # save the Fbx file that contains the linear skinned base mesh and its animation.

    def save_fbx(self):
        # Export animation as an FBX file.
        try:
            base_meshes = []
            for mesh_mapping in self.generator_config.mesh_mappings:
                base_meshes.append(mesh_mapping.base_mesh_name)
                
            result = fbx_export(
                self.generator_config.output_fbx_file,
                selected_meshes = base_meshes,
                start_frame=0,
                end_frame=self.generator_config.start_frame + self.generator_config.num_samples - 1,
            )
            return True, ''
        except Exception as message:
            return False, str(message)

    # save the Alembic file that contains the target mesh and its animation.
    def save_alembic(self):
        # Select the target mesh.
        target_meshes = []
        for mesh_mapping in self.generator_config.mesh_mappings:
            target_meshes.append(mesh_mapping.target_mesh_name)
        try:
            abc_export(
                self.generator_config.output_abc_file,
                roots=target_meshes,
                take_start_frame=0,
                take_end_frame=self.generator_config.start_frame + self.generator_config.num_samples - 1)
            return True, ''
        except Exception as message:
            traceback.print_exc()
            return False, str(message)

    # Check if we can handle this attribute.
    # Basically we can't really handle attributes that are structures for now.
    def get_can_handle_attribute(self, parameter_name, attribute_name):
        return attribute_name.count('.') == 0

    # Check whether the parameter actually still exists in the scene.
    # This might change when users delete objects after already adding parameters.
    def get_parameter_exists(self, param_index):
        parameter = self.generator_config.parameters[param_index]
        left_dot_index = parameter.name.find('.')
        assert left_dot_index != -1, 'Expected to find a dot in the parameter name.'
        object_name = parameter.name[:left_dot_index]
        attribute_name = parameter.name[left_dot_index + 1:]
        if cmds.objExists(object_name):
            return cmds.attributeQuery(attribute_name, node=object_name, exists=True)
        return False

    def get_attribute_values(self, attribute_name, node_name):
        min_value = None
        max_value = None
        default_value = 0.0

        # If the attribute exists.
        if cmds.attributeQuery(attribute_name, node=node_name, exists=True):
            # If the minimum value exists.
            if cmds.attributeQuery(attribute_name, node=node_name, minExists=True):
                min_value = cmds.attributeQuery(attribute_name, node=node_name, minimum=True)[0]

            # If the maximum value exists.
            if cmds.attributeQuery(attribute_name, node=node_name, maxExists=True):
                max_value = cmds.attributeQuery(attribute_name, node=node_name, maximum=True)[0]

            # Get the default value.
            default_value = cmds.attributeQuery(attribute_name, node=node_name, listDefault=True)[0]

        return default_value, min_value, max_value

    # Return the parent attribute name or None if the attribute has no parent
    def get_attribute_group_name(self,  attribute_name, node_name):
        short_object_name = cmds.ls(node_name)[0]
        if cmds.attributeQuery(attribute_name, node=node_name, exists=True):
            parent_attribute = cmds.attributeQuery(attribute_name, node=node_name, listParent=True)
            if parent_attribute:
                return short_object_name + "." + parent_attribute[0]
        return short_object_name + "." + attribute_name

    # Find a given attribute in the defaults list.
    def find_attribute_min_max(self, attribute_name):
        results = [attribute for attribute in self.attribute_min_max_values if
                   attribute.name.lower() == attribute_name.lower()]
        if len(results) > 0:
            return results[-1]
        return None

    # Get the list of meshes.
    def get_mesh_list(self):
        mesh_list = list()

        shapes_list = cmds.ls(selection=False, long=True, objectsOnly=True, geometry=True, type='mesh')
        if shapes_list:
            mesh_list = cmds.listRelatives(shapes_list, parent=True)
            mesh_list = sorted(set(mesh_list))  # Remove duplicates and sort by name

        return mesh_list

    # Extract rotation limits from a joint in Maya.
    def get_rotation_limits(self, joint_name, object_type_string):
        limit_info = JointLimit()

        if not object_type_string:
            object_type_string = cmds.getType(joint_name)

        if object_type_string != 'joint':
            return False, limit_info

        # Get joint limits.
        query_results = cmds.joint(
            joint_name,
            q=True,
            limitSwitchX=True,
            limitSwitchY=True,
            limitSwitchZ=True,
            limitX=True,
            limitY=True,
            limitZ=True)

        limit_info.min_rot_limit_x = query_results[0]
        limit_info.max_rot_limit_x = query_results[1]
        limit_info.min_rot_limit_y = query_results[2]
        limit_info.max_rot_limit_y = query_results[3]
        limit_info.min_rot_limit_z = query_results[4]
        limit_info.max_rot_limit_z = query_results[5]
        limit_info.has_min_rot_limit_x = query_results[6]
        limit_info.has_max_rot_limit_x = query_results[7]
        limit_info.has_min_rot_limit_y = query_results[8]
        limit_info.has_max_rot_limit_y = query_results[9]
        limit_info.has_min_rot_limit_z = query_results[10]
        limit_info.has_max_rot_limit_z = query_results[11]
        return True, limit_info

    # Apply Maya's joint limits.
    def apply_maya_limits(self, long_channel_name, limit_info, min_value, max_value):
        if long_channel_name == 'rotateX':
            if limit_info.has_min_rot_limit_x: min_value = limit_info.min_rot_limit_x
            if limit_info.has_max_rot_limit_x: max_value = limit_info.max_rot_limit_x
        elif long_channel_name == 'rotateY':
            if limit_info.has_min_rot_limit_y: min_value = limit_info.min_rot_limit_y
            if limit_info.has_max_rot_limit_y: max_value = limit_info.max_rot_limit_y
        elif long_channel_name == 'rotateZ':
            if limit_info.has_min_rot_limit_z: min_value = limit_info.min_rot_limit_z
            if limit_info.has_max_rot_limit_z: max_value = limit_info.max_rot_limit_z

        return min_value, max_value

    # Return channels that are selected in the channelbox.
    def find_parameters(self, filter_settings):
        # Get the selected objects.
        selected_objects = cmds.ls(selection=True, long=True, objectsOnly=True)
        if not selected_objects:
            return list()

        # Get all selected objects that aren't shapes and include their children if wanted.
        relatives = list()
        if filter_settings.include_children:
            relatives = cmds.listRelatives(selected_objects, children=filter_settings.include_children,
                                           allDescendents=True, shapes=False, fullPath=True, path=True)
        if relatives:
            selected_objects.extend(relatives)

        # Add shapes.
        if filter_settings.include_shapes:
            shapes = cmds.listRelatives(selected_objects, children=filter_settings.include_children, allDescendents=True,
                                        shapes=True, path=True)
            if shapes:
                selected_objects.extend(shapes)

        if not selected_objects:
            return list()

        # Remove duplicates.
        unique_objects = list(set(selected_objects))

        # Filter out the types we are interested in.
        included_object_types = list()
        excluded_object_types = list()
        objects = list()

        if filter_settings.include_transforms:
            included_object_types.append('transform')

        if filter_settings.include_joints:
            included_object_types.append('joint')

        for type_string in filter_settings.include_custom_types:
            included_object_types.append(type_string)

        for type_string in filter_settings.exclude_custom_types:
            excluded_object_types.append(type_string)

        if filter_settings.include_all:
            if len(excluded_object_types) > 0:
                for cur_object in unique_objects:
                    object_type = cmds.objectType(cur_object)
                    if object_type.lower() not in (item.lower() for item in excluded_object_types):
                        objects.append(cur_object)
            else:
                objects = unique_objects[:]
        else:
            for cur_object in unique_objects:
                object_type = cmds.objectType(cur_object)
                if object_type.lower() in (item.lower() for item in included_object_types):
                    objects.append(cur_object)

        # Get the attributes.
        parameters = list()
        channels = list()
        if filter_settings.selected_channels_only:
            channel_box_name = mel.eval('$temp=$gChannelBoxName')
            sma = cmds.channelBox(channel_box_name, query=True, selectedMainAttributes=True)
            ssa = cmds.channelBox(channel_box_name, query=True, selectedShapeAttributes=True)
            sha = cmds.channelBox(channel_box_name, query=True, selectedHistoryAttributes=True)
            if sma:
                channels.extend(sma)
            if ssa:
                channels.extend(ssa)
            if sha:
                channels.extend(sha)

            for object in objects:
                object_type = cmds.objectType(object)

                # Get rotation limits if they exist (internally checks whether it's a joint etc).
                has_limit_info, limit_info = self.get_rotation_limits(object, object_type)

                for channel in channels:
                    attribute_exists = cmds.attributeQuery(channel, node=object, exists=True)
                    if attribute_exists:
                        long_channel_name = cmds.attributeQuery(channel, node=object, longName=True)

                        if long_channel_name.lower() in (item.lower() for item in filter_settings.exclude_attributes):
                            continue

                        full_path_name = object + '.' + long_channel_name
                        if not self.get_can_handle_attribute(full_path_name, long_channel_name):
                            # print('Cannot handle attribute: {} for object {}'.format(full_path_name, object))
                            continue

                        # Skip locked attributes.
                        locked = cmds.getAttr(full_path_name, lock=True)
                        if locked:
                            continue

                        # Skip attributes we already have added.
                        if any(x.name == full_path_name for x in self.generator_config.parameters):
                            continue

                        # Figure out the min and max values.
                        default_value, min_value, max_value = self.get_attribute_values(long_channel_name, object)
                        attribute_min_max = self.find_attribute_min_max(long_channel_name)
                        if not min_value:
                            min_value = attribute_min_max.min_value if attribute_min_max else 0.0
                        if not max_value:
                            max_value = attribute_min_max.max_value if attribute_min_max else 1.0

                        # Overwrite with Maya joint limits if they exist.
                        if has_limit_info:
                            min_value, max_value = self.apply_maya_limits(long_channel_name, limit_info, min_value,
                                                                          max_value)

                        # Get the short object name.
                        short_object_name = cmds.ls(object)[0]
                        pipe_index = short_object_name.rfind('|')
                        if pipe_index != -1:
                            short_object_name = short_object_name[pipe_index + 1:]

                        # Add the parameter to the list.
                        new_param = Parameter()
                        new_param.name = full_path_name
                        new_param.display_name = short_object_name + '.' + long_channel_name
                        new_param.object_type = object_type
                        new_param.min_value = min_value
                        new_param.max_value = max_value
                        new_param.default_value = default_value
                        new_param.group_name = self.get_attribute_group_name(long_channel_name, object)
                        parameters.append(new_param)
        else:  # Get all keyable attributes.
            for object in objects:
                object_type = cmds.objectType(object)

                # Get rotation limits if they exist (internally checks whether its a Joint etc).
                has_limit_info, limit_info = self.get_rotation_limits(object, object_type)

                channels = cmds.listAttr(object, keyable=True, scalar=True, visible=True, settable=True, inUse=True)
                if channels:
                    for long_channel_name in channels:
                        if long_channel_name.lower() in (item.lower() for item in filter_settings.exclude_attributes):
                            continue

                        full_path_name = object + '.' + long_channel_name
                        if not self.get_can_handle_attribute(full_path_name, long_channel_name):
                            # print('Cannot handle attribute: {} for object {}'.format(full_path_name, object))
                            continue

                        # Skip locked attributes.
                        locked = cmds.getAttr(full_path_name, lock=True)
                        if locked:
                            continue

                        # Skip attributes we already have added.
                        if any(x.name == full_path_name for x in self.generator_config.parameters):
                            continue

                        # Figure out the min and max values.
                        default_value, min_value, max_value = self.get_attribute_values(long_channel_name, object)
                        attribute_min_max = self.find_attribute_min_max(long_channel_name)
                        if not min_value:
                            min_value = attribute_min_max.min_value if attribute_min_max else 0.0
                        if not max_value:
                            max_value = attribute_min_max.max_value if attribute_min_max else 1.0

                        # Overwrite with Maya joint limits if they exist.
                        if has_limit_info:
                            min_value, max_value = self.apply_maya_limits(long_channel_name, limit_info, min_value,
                                                                          max_value)

                        # Get the short object name.
                        short_object_name = cmds.ls(object)[0]
                        pipe_index = short_object_name.rfind('|')
                        if pipe_index != -1:
                            short_object_name = short_object_name[pipe_index + 1:]

                        # Add the parameter.
                        new_param = Parameter()
                        new_param.name = full_path_name
                        new_param.display_name = short_object_name + '.' + long_channel_name
                        new_param.object_type = object_type
                        new_param.min_value = min_value
                        new_param.max_value = max_value
                        new_param.default_value = default_value
                        new_param.group_name = self.get_attribute_group_name(long_channel_name, object)
                        parameters.append(new_param)

        # Sort parameters on display name.
        if len(parameters) > 0:
            parameters.sort(key=lambda x: x.display_name.lower())
        return parameters
