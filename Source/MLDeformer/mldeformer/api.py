# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

from mldeformer.ui.maya.maya_event_handler import MayaEventHandler
from mldeformer.ui.parameter import Parameter
# Add the parameters from the add params window to this.
import sys
import copy 

# the api module
api_module = sys.modules[__name__]

# module variable
api_module.iface = None


class DeformerInterface(object):
    def __init__(self):
        self.event_handler = MayaEventHandler()
        if self.event_handler.global_settings.auto_load_last_config:
            self.event_handler.generator_config.load_from_file(self.event_handler.last_config_file)

    def has_parameter(self, parameter_name):
        return self.event_handler.generator_config.has_parameter(parameter_name)
    
    def add_parameter(self, name, display_name=None, default_value=0.0, min_value =0.0, max_value = 1.0, object_type = "joint"):
        new_param = Parameter()
        new_param.name = name
        new_param.display_name = display_name or name
        new_param.object_type = object_type
        new_param.min_value = min_value
        new_param.max_value = max_value
        new_param.default_value = default_value
        if not self.event_handler.generator_config.has_parameter(name):
            self.event_handler.generator_config.parameters.append(new_param)
    
    def get_parameter(self, name):
        for param in self.event_handler.generator_config.parameters:
            if param.name == name:
                return param

        raise ValueError("The provided parameter is not in the configuration")
    
    def set_parameter(self, in_parameter):
        for param in self.event_handler.generator_config.parameters:
            if param.name == in_parameter.name:
                param = in_parameter
                return True

        raise ValueError("The provided parameter is not in the configuration")
    
    def list_parameters(self):
        all_params = [param.name for param in self.event_handler.generator_config.parameters]
        return all_params
    
    def generate_samples(self):
        return self.event_handler.generate()

    def export_fbx_and_abc(self, output_fbx_file, output_abc_file):
        old_fbx = self.event_handler.generator_config.output_fbx_file
        old_abc = self.event_handler.generator_config.output_abc_file
        self.event_handler.generator_config.output_fbx_file = output_fbx_file
       
        saved_fbx, fbx_error_message = self.event_handler.save_fbx()
        self.event_handler.generator_config.output_fbx_file = old_fbx
        if not saved_fbx:
            return False

        # save the Alembic if we enabled exporting it, and if there is actually a target mesh.
        if self.event_handler.get_first_enabled_mesh_mapping_index_with_target_mesh() != -1:
            self.event_handler.generator_config.output_abc_file = output_abc_file
            saved_alembic, abc_error_message = self.event_handler.save_alembic()
            self.event_handler.generator_config.output_abc_file = old_abc
            if not saved_alembic:
                return False
        return True

    def load_config(self, config_file):
        self.event_handler.generator_config.load_from_file(config_file)
        
    def save_config(self, config_file):
        self.event_handler.generator_config.save_to_file(config_file)


def _create_deformer_api_interface():
    if api_module.iface is None:
        api_module.iface = DeformerInterface()


def has_parameter(parameter_name):
    """Returns if the parameter with the given name exists

       Arguments:
           parameter_name(string, required): The name of the parameter to test

      Example: 
          >>> from mldeformer import api as ml_api 
          >>> param = ml_api.get_parameter("example_joint")
          >>> print(param.default_value)

      """
    _create_deformer_api_interface()
    return api_module.iface.has_parameter(parameter_name)


def add_parameter(name, display_name=None, default_value=0.0, min_value =0.0, max_value = 1.0, object_type = "joint"):
    """Add a new parameter with the given name

       Arguments:
           name(string, required): The name of the parameter to add
           display_name(string, optional): The display name of the parameter
           default_value(float, optional): The default value of the parameter
           min_value(float, optional): The minimum value of the parameter
           max_value(float, optional): The maximum value of the parameter
           object_type(string, optional): The type of the parameter (joint, blendshape etc.)

      Example: 
          >>> from mldeformer import api as ml_api 
          >>> param = ml_api.add_parameter("example_joint", default_value=0.5, min_value=-1.0, max_value=1.0)

      """
    _create_deformer_api_interface()
    return api_module.iface.add_parameter(name, display_name, default_value, min_value,
                                                       max_value, object_type)


def get_parameter(parameter_name):
    """Returns a parameter with the given name

    A parameter is a  Class with the following properties: name, display_name, default_value, min_value, 
    max_value, object_type

     Arguments:
         parameter_name(string, required): The name of the parameter to find

    Example: 
        >>> from mldeformer import api as ml_api 
        >>> param = ml_api.get_parameter("example_joint")
        >>> print(param.default_value)

    """
    _create_deformer_api_interface()
    return copy.copy(api_module.iface.get_parameter(parameter_name))


def set_parameter(parameter):
    """Set a parameter with new values. 

    A parameter is a  Class with the following properties: name, display_name, default_value, min_value, 
    max_value, object_type
    
     Arguments:
         parameter(ui.parameters.Parameter): A ui.parameters.Parameter class to set

    Example: 
        >>> from mldeformer import api as ml_api 
        >>> param_details = ml_api.get_parameter("example_joint")
        >>> param_details.default_value = 0.5
        >>> ml_api.set_parameter(param_details) 
    """
    _create_deformer_api_interface()
    return api_module.iface.set_parameter(parameter)


def list_parameters():
    """Returns a list containing the names of all parameters in the generator. 
     
     The returned name can be used in get_parameter to access the ui.parameter.Parameter class used by the generator
    Example: 
        >>> from mldeformer import api as ml_api 
        >>> params = ml_api.list_parameters()
        >>> for param_name in params: 
        >>>     param_details = ml_api.get_parameter(param_name)
        >>>     print(param_details)
    """
    _create_deformer_api_interface()
    return api_module.iface.list_parameters()


def generate_samples(start_frame=0, end_frame=1000,
                     controller_probability=0.2, set_range_limit_probability=0.01,
                     random_seed=7777):
    """Generate samples given the current parameter settings

    This function executes the mldeformer.generator.maya.pose_generator to create random animation on the 
    parameters in the generator.  

    Arguments:
        start_frame (int, optional): The first frame to start generating samples
        end_frame (int, optional): The last frame of the generated samples
        controller_probability (float, optional): Probability of a controller activating
        set_range_limit_probability (float, optional): Probability of making a controller the max or min value
        random_seed:(int, optional): The seed value used by the random number generator

    Example: 
        >>> from mldeformer import api as ml_api 
        >>> ml_api.generate_samples(start_frame=100, end_frame=500)
    """

    _create_deformer_api_interface()
    
    deformer_config = api_module.iface.event_handler.generator_config
    previous_config = copy.copy(deformer_config)
    
    deformer_config.start_frame = start_frame
    deformer_config.num_samples = end_frame - start_frame
    deformer_config.controller_probability = controller_probability
    deformer_config.set_max_probability = set_range_limit_probability
    
    deformer_config.random_seed = random_seed

    generate_results = api_module.iface.generate_samples()

    api_module.iface.event_handler.generator_config = previous_config

    return generate_results


def export_fbx_and_abc(output_fbx_file, output_abc_file):
    """Export samples to a fbx file and alembic cache  

        Arguments:
            output_fbx_file (string, required): The path to the fbx file
            output_abc_file (string, required): The path to the abc file

    """

    _create_deformer_api_interface()
    return api_module.iface.export_fbx_and_abc(output_fbx_file, output_abc_file)


def load_config(config_file):
    """Load a configuration file for the mldeformer generator

        Arguments:
            config_file (string, required): The path to the config file

    """

    _create_deformer_api_interface()
    return api_module.iface.load_config(config_file)


def save_config(config_file):
    """Save a configuration file for the mldeformer generator

    Arguments:
        config_file (string, required): The path to the config file

    Example:
    >>> from mldeformer import api as ml_api 
    >>> ml_api.save_config('D:\\testconfig.json')
    """

    _create_deformer_api_interface()
    return api_module.iface.save_config(config_file)
