# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as omanim
import math

try:
    from itertools import izip
except ImportError:  #python3.x
    izip = zip

# Keyframe animation class
class KeyFrameAnimation():
    """KeyFrameAnimation """

    def __init__(self):
        """ Initialize KeyFrameAnimation class. """
        # Inititalize controller and attribute list.
        self.ctrl_list = []
        self.attr_list = []
        self.attr_times = om.MTimeArray()
        self.attr_values = []
        # Default input and output animation curve types.
        self.in_curve_type = 'linear'
        self.out_curve_type = 'linear'
        # Start and end time
        self.start_time = 0
        self.end_time = 0

    def set_controller_attribute(self, ctrl, attr):
        """"Set controller and attribute name.
        Parameters:
            ctrl (str) -- Controller name
            attr (str) -- Attribute name
        """
        self.ctrl_list.append(ctrl)
        self.attr_list.append(attr)

    def set_controller_attributes(self, ctrl_attr_list):
        """"Create a list of controller and attributes from a joint list.
        Parameters:
            ctrl_attr_list (str) -- Controller attribute list, each element separated by '.'
        """
        for ctrl_attr in ctrl_attr_list:
            ctrl, attr = ctrl_attr.split('.')
            self.ctrl_list.append(ctrl)
            self.attr_list.append(attr)
            self.attr_values.append(om.MDoubleArray())

    def set_animation_curve_types(self, in_type, out_type):
        """"Set the input and output animation curves.
        Parameters:
            in_type (str)  -- Input animation curve type
            out_type (str) -- Output animation curve type
        """
        self.in_curve_type = in_type
        self.out_curve_type = out_type

    def set_interval(self, start_time, end_time):
        """"Set key frames.
        Parameters:
            start_time (int) -- Start time for animation
            end_time (int)   -- End time for animation
        """
        self.start_time = start_time
        self.end_time = end_time

    def set_keyframe(self, in_val, out_val=None, idx=0):
        """"Set key frame.
        Parameters:
            in_val (float)  -- Initial value
            out_val (float) -- Output value
            idx (int)       -- list index
        """
        ctrl_name = self.ctrl_list[idx]
        attr_name = self.attr_list[idx]
        # Set start and end time of loop.
        if out_val is not None and self.start_time != self.end_time:
            cmds.setKeyframe(ctrl_name, time=self.start_time, attribute=attr_name, value=in_val)
            cmds.setKeyframe(ctrl_name, time=self.end_time, attribute=attr_name, value=out_val)
        else:
            cmds.setKeyframe(ctrl_name, time=self.start_time, attribute=attr_name, value=in_val)
        # Select the animation time.
        cmds.selectKey(ctrl_name, time=(self.start_time, self.end_time), attribute=attr_name)
        # Set the animation curve as linear
        cmds.keyTangent(inTangentType=self.in_curve_type, outTangentType=self.out_curve_type)

    def set_keyframes(self, in_val_list, out_val_list=None):
        """"Set key frames.
        Parameters:
            in_val_list (list(float))  -- Initial values
            out_val_list (list(float)) -- Output values, if any
        """
        idx = 0
        if out_val_list is not None:
            for in_val, out_val in izip(in_val_list, out_val_list):
                self.set_keyframe(in_val=in_val, out_val=out_val, idx=idx)
                idx += 1
        else:
            for in_val in in_val_list:
                self.set_keyframe(in_val=in_val, idx=idx)
                idx += 1

    @staticmethod
    def remove_keyframes(start_time=0, end_time=-1):
        """"Remove all keyframes from all active objects (full purge).
        Parameters:
            start_time (int) -- Start time in time slider
            end_time (int)   -- End time in time slider
        """
        if end_time >= start_time:
            cmds.cutKey(time=(start_time, end_time))

    @staticmethod
    def keyframes_exist(start_time, end_time):
        """"Check if keyframes exist in user-specified range.
        Parameters:
            start_time (int) -- Start time
            end_time (int)   -- End time
        Return:
            True if keyframes in range; otherwise false.
        """
        if end_time >= start_time:
            found_time = cmds.findKeyframe(
                timeSlider=True, time=(start_time, end_time), which="next")
            if found_time < end_time:
                return True
            return False
        else:
            found_time = cmds.findKeyframe(
                timeSlider=True, time=(start_time, end_time), which="previous")
            if found_time > end_time:
                return True
            return False

    def store_keyframes(self, frame_time, in_val_list):
        """"Set key frames.
        Parameters:
            frame_time    -- time of the key frame
            in_val_list   -- list of values to store - these value match the indices in ctrl_list
        """
        idx = 0
        self.attr_times.append(om.MTime(frame_time, om.MTime.uiUnit()))
        for in_val in in_val_list:
            self.attr_values[idx].append(in_val)
            idx += 1

    @staticmethod
    def om_set_keyframes(ctrl_name, attr_name, key_times, key_values):
        """"Set key frames at once using the open maya api
        Parameters:
            ctrl_name -- Control Name
            attr_name -- Attribute Name
            key_times
            key_values
        """
        omslist = om.MSelectionList()
        omslist.add("{0}.{1}".format(ctrl_name, attr_name))
        mplug = omslist.getPlug(0)
        mcurve = omanim.MFnAnimCurve(mplug)
        try:
            mcurve.name()  # errors if does not exist
        except:
            mcurve.create(mplug)  # if the curve does not exist, create it and attach it to the plug

        angular_types = [omanim.MFnAnimCurve.kAnimCurveTA, omanim.MFnAnimCurve.kAnimCurveUA]
        if mcurve.animCurveType in angular_types:
            key_values = [math.radians(i) for i in key_values]

        mcurve.addKeys(
            key_times,
            key_values,
            omanim.MFnAnimCurve.kTangentStep,
            omanim.MFnAnimCurve.kTangentStep,
            True)

    def set_all_stored_keyframes(self):
        """"Set all key frames stored with store_keyframes.
        """
        idx = 0
        for ctrl_name in self.ctrl_list:
            attr_name = self.attr_list[idx]
            self.om_set_keyframes(ctrl_name, attr_name, self.attr_times, self.attr_values[idx])
            idx += 1
