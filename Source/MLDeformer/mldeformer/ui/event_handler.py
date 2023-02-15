# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

import json
import os
from os.path import expanduser
import traceback

from .attribute_minmax import AttributeMinMax
from .config import Config
from .json_encoder import JsonEncoder
from .global_settings import GlobalSettings
from mldeformer.generator.maya.generation import pose_generator

# Event handler base class.
class EventHandler(object):
    def __init__(self):
        self.attribute_min_max_values = list()
        self.global_settings = GlobalSettings()

        user_home_folder = expanduser('~')
        base_deformer_path = os.path.join(user_home_folder, 'UE_MLDeformer')
        dcc_name = self.get_dcc_name()
        self.rig_deformer_path = os.path.join(base_deformer_path, dcc_name)
        self.output_path = os.path.join(base_deformer_path, 'Output')
        print('[MLDeformer] Settings folder used: {}'.format(self.rig_deformer_path))
        try:
            os.mkdir(base_deformer_path)
        except:
            pass

        try:
            os.mkdir(self.output_path)
        except:
            pass

        try:
            os.mkdir(self.rig_deformer_path)
        except:
            pass

        self.last_config_file = os.path.join(self.rig_deformer_path, 'LastConfig.config')
        self.last_filter_settings_file = os.path.join(self.rig_deformer_path, 'LastFilterSettings.filterSettings')
        self.min_max_settings_file = os.path.join(self.rig_deformer_path, 'AttributeMinMaxSetup.minMaxSetup')
        self.global_settings_file = os.path.join(self.rig_deformer_path, 'GlobalSettings.globalSettings')
        self.global_settings.load_from_file(self.global_settings_file)

        # Get the icon file paths.
        self.main_python_folder = os.path.dirname(os.path.abspath(__file__))
        self.icon_folder = os.path.join(self.main_python_folder, 'qtgui')
        self.icon_folder = os.path.join(self.icon_folder, 'icons')
        self.unreal_icon_path = os.path.join(self.icon_folder, 'unreal.png')
        self.add_icon_path = os.path.join(self.icon_folder, 'add.png')
        self.open_icon_path = os.path.join(self.icon_folder, 'open.png')
        self.refresh_icon_path = os.path.join(self.icon_folder, 'refresh.png')
        self.save_icon_path = os.path.join(self.icon_folder, 'save.png')

        self.generator_config = Config(self.output_path)

        if not self.load_attribute_min_max_setup_from_file(self.min_max_settings_file):
            self.register_default_min_max_setup()

    # Register default min and max setups. You can overload this and append data to the attribute_min_max_values list.
    def register_default_min_max_setup(self):
        pass

    # Register the default filter settings. Modify the filter member in here. You can overload this function.
    # The filter parameter is a MLDeformerParameterFilter object.
    def register_default_filter_settings(self, filter):
        pass

    # Get the parent window.
    def get_parent_window(self):
        raise Exception('Please implement the GetParentWindow function inside your derived event handler!')
        # return None

    # Check whether the parameter actually still exists in the scene.
    # This might change when users delete objects after already adding parameters.
    def get_parameter_exists(self, param_index):
        raise Exception('Please implement the get_parameter_exists function inside your derived event handler!')
        # return True

    # Get the DCC name, for example 'Maya' or 'Blender'.
    def get_dcc_name(self):
        raise Exception('Please implement the get_dcc_name function inside your derived event handler!')

    # save the Fbx file that contains the linear skinned base mesh and its animation.
    # This has to return a boolean and error message that will be displayed when False is returned.
    def save_fbx(self):
        raise Exception('Please implement the save_fbx function in your derived event handler!')

    # save the Alembic file that contains the target mesh and its animation.
    # This has to return a boolean and error message that will be displayed when False is returned.
    def save_alembic(self):
        raise Exception('Please implement the save_alembic function in your derived event handler!')

    # Get a list of meshes.
    def get_mesh_list(self):
        raise Exception('Please implement the get_mesh_list function in your derived event handler!')
        # mesh_list = list()
        # ...fill list with strings...
        # return mesh_list

    def get_selected_mesh_list(self):
        raise Exception('Please implement the get_selected_mesh_list function in your derived event handler!')
        # mesh_list = list()
        # ...fill list with strings...
        # return mesh_list

    # Start a new progress bar session.
    def start_progress_bar(self, status_text='Processing...', interruptable=True):
        raise Exception('Please implement the start_progress_bar function in your derived event handler!')

    # Set the progress bar progress percentage.
    def set_progress_bar_value(self, progress_percentage):
        raise Exception('Please implement the set_progress_bar_value function in your derived event handler!')

    # Does the user want to cancel progress?
    def is_progress_bar_cancelled(self):
        raise Exception('Please implement the is_progress_bar_cancelled function in your derived event handler!')

    # Stop the progress bar session.
    def stop_progress_bar(self):
        raise Exception('Please implement the stop_progress_bar function in your derived event handler!')

    # generate the frames in the DCC scene.
    def generate(self):
        try:
            return pose_generator.generate_samples_from_gui(self)
        except Exception as message:
            traceback.print_exc()
            print(str(message))
            return False, str(message)

    # save the attribute min/max setup to a file.
    def save_attribute_min_max_setup_to_file(self, filename):
        data = json.dumps(self.attribute_min_max_values, sort_keys=True, indent=4, cls=JsonEncoder)
        with open(filename, 'wt') as writeFile:
            writeFile.writelines(data)

    def load_global_settings_from_file(self, file_path):
        self.global_settings.load_from_file(file_path)

    def load_attribute_min_max_setup_from_file(self, filename):
        json_string = ''
        try:
            with open(filename, 'rt') as readFile:
                json_string = readFile.readlines()
                if len(json_string) > 0:
                    json_string = ' '.join(json_string)  # Turn the list of strings into one string.
                    data = json.loads(json_string)
                    del self.attribute_min_max_values[:]
                    for item in data:
                        new_min_max = AttributeMinMax(item['name'], float(item['min_value']),
                                                      float(item['max_value']))
                        self.attribute_min_max_values.append(new_min_max)
        except:
            del self.attribute_min_max_values[:]
            return False
        return True

    def get_selected_channels(self):
        return list()

    def get_first_enabled_mesh_mapping_index(self):
        for mapping_index, mapping in enumerate(self.generator_config.mesh_mappings):
            if mapping.is_enabled:
                return mapping_index
        return -1

    def get_first_enabled_mesh_mapping_index_with_target_mesh(self):
        for mapping_index, mapping in enumerate(self.generator_config.mesh_mappings):
            if mapping.is_enabled and mapping.target_mesh_name:
                return mapping_index
        return -1

    def has_min_max_item_errors(self, index):
        min_max_object = self.attribute_min_max_values[index]
        return (min_max_object.min_value > min_max_object.max_value)

    def has_min_max_errors(self):
        for index in range(0, len(self.attribute_min_max_values)):
            if self.has_min_max_item_errors(index):
                return True
        return False
