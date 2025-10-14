# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

import os
import json

from mldeformer.ui.Qt import QtCore, QtGui, QtWidgets
from mldeformer.ui.qtgui.helpers import QtHelpers
from mldeformer.ui.qtgui.folder_picker_field_widget import FolderPickerFieldWidget
from mldeformer.ui.qtgui.joint_picker_window import JointPickerWindow
from mldeformer.ui.qtgui.filter_widget import FilterWidget
from mldeformer.ui.recent_file_list import RecentFileList

import mldeformer.optional_numpy


class PoseExtractionJsonEncoder(json.JSONEncoder):
    def default(self, object):
        if isinstance(object, PoseExtractionConfig):
            return object.__dict__
        else:
            return json.JSONEncoder.default(self, object)


class PoseExtractionConfig:
    def __init__(self):
        self.auto_load_last_config = False
        self.fbx_input_folder = os.path.expanduser('~')
        self.num_output_poses = 5000
        self.max_frames_per_fbx = 100000
        self.joint_list = list()

    def load_from_file(self, path: str):
        with open(path, 'rt') as readFile:
            json_string = readFile.readlines()
            if len(json_string) > 0:
                json_string = ' '.join(json_string)  # Turn the list of strings into one string.
                data = json.loads(json_string)
                self.init_from_json_data(data)

    def save_to_file(self, path: str):
        json_string = json.dumps(self, sort_keys=True, indent=4, cls=PoseExtractionJsonEncoder)
        with open(path, 'wt') as writeFile:
            writeFile.writelines(json_string)

    def init_from_json_data(self, config_data):
        if 'auto_load_last_config' in config_data: self.auto_load_last_config = config_data['auto_load_last_config']
        if 'fbx_input_folder' in config_data: self.fbx_input_folder = config_data['fbx_input_folder']
        if 'num_output_poses' in config_data: self.num_output_poses = config_data['num_output_poses']
        if 'max_frames_per_fbx' in config_data: self.max_frames_per_fbx = config_data['max_frames_per_fbx']
        if 'joint_list' in config_data: self.joint_list = config_data['joint_list']


class PoseExtractionWindow(QtWidgets.QMainWindow):
    main_button_size = 22

    def __init__(self, event_handler):
        super(PoseExtractionWindow, self).__init__(event_handler.get_parent_window())

        self.config = PoseExtractionConfig()
        self.recent_configs_menu = None
        self.filter_text = ''
        self.filter_widget = None
        self.joint_list = list()

        self.fbx_folder_widget = None
        self.num_poses_widget = None
        self.splitter = None
        self.right_side_widget = None
        self.left_side_widget = None
        self.generate_button = None
        self.right_grid_layout = None
        self.add_joint_button = None
        self.left_upper_layout = None
        self.right_side_layout = None
        self.left_side_layout = None
        self.joint_widget = None
        self.max_frames_per_fbx_widget = None
        self.event_handler = event_handler

        self.recent_config_list_file = os.path.join(self.event_handler.rig_deformer_path, 'RecentPoseExtraction.configList')
        self.recent_config_list = RecentFileList()
        self.recent_config_list.load(self.recent_config_list_file)

        self.init_ui()

    def init_ui(self):
        print('[MLDeformer] Creating Pose Extraction UI')

        # Create the main window.
        self.setObjectName('MLDeformerPoseExtractionWindow')
        self.setWindowTitle('ML Deformer (Unreal Engine) - Pose Extraction Tool')
        self.setWindowIcon(QtGui.QIcon(self.event_handler.unreal_icon_path))
        self.resize(850, 600)

        self.create_main_menu()

        # Create a left and right side widgets and layouts.
        self.left_side_widget = QtWidgets.QWidget()
        self.right_side_widget = QtWidgets.QWidget()
        self.left_side_layout = QtWidgets.QVBoxLayout(self.left_side_widget)
        self.right_side_layout = QtWidgets.QVBoxLayout(self.right_side_widget)

        # Create the splitter in the center of the window, which splits the left and right side of the UI.
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.setCentralWidget(self.splitter)
        self.splitter.addWidget(self.left_side_widget)
        self.splitter.addWidget(self.right_side_widget)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)

        ######################################################################
        # Left Side of UI.
        ######################################################################
        # Create the horizontal layout for buttons, above the listbox.
        self.left_upper_layout = QtWidgets.QHBoxLayout()
        self.left_side_layout.addLayout(self.left_upper_layout)

        # Create the joint list text item.
        list_label = QtWidgets.QLabel('Joint List:')
        list_label.setStyleSheet('color: orange')
        self.left_upper_layout.addWidget(list_label)

        # Add a filler.
        filler_widget = QtWidgets.QWidget()
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        filler_widget.setSizePolicy(size_policy)
        self.left_upper_layout.addWidget(filler_widget)

        # Create the search filter widget.
        self.filter_widget = FilterWidget(fixed_height_value=22)
        self.filter_widget.setMaximumWidth(400)
        self.filter_widget.text_changed.connect(self.on_filter_text_changed)
        self.left_upper_layout.addWidget(self.filter_widget)

        # Create the add button.
        self.add_joint_button = QtWidgets.QPushButton(QtGui.QIcon(self.event_handler.add_icon_path), '')
        self.add_joint_button.setStyleSheet('background-color: green')
        self.add_joint_button.setFixedSize(self.main_button_size, self.main_button_size)
        self.add_joint_button.clicked.connect(self.on_add_joints_button_pressed)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.add_joint_button.setSizePolicy(size_policy)
        self.add_joint_button.setToolTip('Add joints to the list.')
        self.left_upper_layout.addWidget(self.add_joint_button)

        # Add the joint list.
        self.joint_widget = QtWidgets.QListWidget()
        self.joint_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.joint_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.joint_widget.customContextMenuRequested.connect(self.on_joint_widget_context_menu)

        self.left_side_layout.addWidget(self.joint_widget)

        ######################################################################
        # Right Side of UI.
        ######################################################################               
        self.right_grid_layout = QtWidgets.QGridLayout()
        self.right_side_layout.addLayout(self.right_grid_layout)

        # Create the Fbx folder picker.
        self.fbx_folder_widget = FolderPickerFieldWidget(self.event_handler, self.config.fbx_input_folder, 'The folder used to load Fbx files from.')
        self.fbx_folder_widget.folder_picked.connect(self.on_fbx_folder_changed)
        name_label, _ = QtHelpers.add_widget_field(self.right_grid_layout,
                                                   row_index=0,
                                                   name='Fbx Input Folder:',
                                                   widget=self.fbx_folder_widget,
                                                   min_label_text_width=120,
                                                   label_alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        name_label.setAlignment(QtCore.Qt.AlignLeft)

        # Number of target poses.
        name_label, self.num_poses_widget = QtHelpers.add_int_field(
            layout=self.right_grid_layout,
            row_index=1,
            name='Num Output Poses:',
            value=self.config.num_output_poses,
            min_value=1,
            max_value=10000000,
            min_label_text_width=120)
        name_label.setAlignment(QtCore.Qt.AlignLeft)

        # Maximum number of frames per Fbx.
        name_label, self.max_frames_per_fbx_widget = QtHelpers.add_int_field(
            layout=self.right_grid_layout,
            row_index=2,
            name='Max Frames Per Fbx:',
            value=self.config.max_frames_per_fbx,
            min_value=1,
            max_value=10000000,
            min_label_text_width=120)
        name_label.setAlignment(QtCore.Qt.AlignLeft)

        # Fill the bottom part of the right side.
        filler_widget = QtWidgets.QWidget()
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        filler_widget.setSizePolicy(size_policy)
        self.right_side_layout.addWidget(filler_widget)

        if mldeformer.optional_numpy.numpy_supported():
            numpy_message_widget = QtWidgets.QLabel('Numpy acceleration active!')
            numpy_message_widget.setStyleSheet('color: rgb(90,150,90)')
        else:
            numpy_message_widget = QtWidgets.QLabel('Warning: Numpy not found, performance can be very slow!')
            numpy_message_widget.setStyleSheet('color: orange')
        self.right_side_layout.addWidget(numpy_message_widget)

        # Add the generate button.
        self.generate_button = QtWidgets.QPushButton('Generate Animation')
        self.generate_button.clicked.connect(self.on_generate_button_pressed)
        self.right_side_layout.addWidget(self.generate_button)

        self.update_generate_button_state()

    # Create the main menu bar.
    def create_main_menu(self):
        main_menu = self.menuBar()
        file_menu = main_menu.addMenu('File')

        configure_menu = main_menu.addMenu('Configure')

        reset_config_action = QtWidgets.QAction('Reset Current Config', self)
        configure_menu.addAction(reset_config_action)
        reset_config_action.setShortcut('Ctrl+R')
        reset_config_action.triggered.connect(self.on_reset_config)

        # Open a config file. 
        open_action = QtWidgets.QAction(QtGui.QIcon(self.event_handler.open_icon_path), 'Load config', self)
        open_action.setShortcut('Ctrl+O')
        file_menu.addAction(open_action)
        open_action.triggered.connect(self.on_load_config)

        # save a config file.
        save_action = QtWidgets.QAction(QtGui.QIcon(self.event_handler.save_icon_path), 'Save config', self)
        save_action.setShortcut('Ctrl+S')
        file_menu.addAction(save_action)
        save_action.triggered.connect(self.on_save_config)

        file_menu.addSeparator()

        self.recent_configs_menu = file_menu.addMenu('Recent Configs')
        self.fill_recent_configs_menu()

    def on_save_config(self):
        # Show the save as dialog.
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption='Save configuration as...',
            dir=self.event_handler.rig_deformer_path,
            filter='Configuration Files (*.poseExtractionConfig)')

        # If we selected a valid filename.
        if len(file_path) > 0:
            self.update_config()
            self.config.save_to_file(file_path)
            self.recent_config_list.add(file_path)
            self.recent_config_list.save(self.recent_config_list_file)

    def on_load_config(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption='Load configuration from...',
            dir=self.event_handler.rig_deformer_path,
            filter='Configuration Files (*.poseExtractionConfig)')

        if len(file_path) > 0:
            self.load_config_file(file_path)

    def update_config(self):
        self.config.fbx_input_folder = self.fbx_folder_widget.get_folder()
        self.config.num_output_poses = self.num_poses_widget.value()
        self.config.max_frames_per_fbx = self.max_frames_per_fbx_widget.value()
        self.config.joint_list = self.joint_list

    def on_reset_config(self):
        self.config = PoseExtractionConfig()
        self.update_ui_widgets_from_config()

    def load_config_file(self, file_path: str, init_ui=True, update_recent_file_list=True):
        self.config.load_from_file(file_path)
        if update_recent_file_list:
            self.recent_config_list.add(file_path)
            self.recent_config_list.save(self.recent_config_list_file)
            self.fill_recent_configs_menu()

        if init_ui:
            self.update_ui_widgets_from_config()

    def fill_recent_configs_menu(self):
        self.recent_configs_menu.clear()
        for path in reversed(self.recent_config_list.file_list):
            filename = os.path.basename(path)
            filename, _ = os.path.splitext(filename)
            action = self.recent_configs_menu.addAction(filename)
            action.setData(path)
            action.triggered.connect(self.on_recent_config)

    def on_recent_config(self):
        action = self.sender()
        self.load_config_file(action.data(), init_ui=True, update_recent_file_list=True)

    def update_ui_widgets_from_config(self):
        self.num_poses_widget.setValue(self.config.num_output_poses)
        self.max_frames_per_fbx_widget.setValue(self.config.max_frames_per_fbx)
        self.fbx_folder_widget.set_folder(self.config.fbx_input_folder)
        self.set_joint_list(self.config.joint_list)

    def update_generate_button_state(self):
        if os.path.exists(self.fbx_folder_widget.get_folder()):
            self.generate_button.setEnabled(True)
            self.generate_button.setToolTip('Generate the animation.')
        else:
            self.generate_button.setEnabled(False)
            self.generate_button.setToolTip('Please make sure your Fbx input folder exists!')

        folder_exists = os.path.exists(self.fbx_folder_widget.get_folder()) and os.path.isdir(self.fbx_folder_widget.get_folder())
        is_enabled = len(self.joint_list) > 0 and folder_exists
        self.generate_button.setEnabled(is_enabled)

    def on_generate_button_pressed(self):
        print('Generate Animation button pressed')
        self.event_handler.execute_pose_extraction(
            fbx_input_folder=os.path.abspath(self.fbx_folder_widget.get_folder()),
            num_output_poses=self.num_poses_widget.value(),
            max_frames_per_fbx=self.max_frames_per_fbx_widget.value(),
            joint_name_list=self.joint_list)

    def on_filter_text_changed(self, new_text: str):
        self.filter_text = new_text
        self.set_joint_list(self.joint_list)

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Delete:
            widget = QtWidgets.QApplication.focusWidget()
            if widget == self.joint_widget:
                self.remove_selected_joints()

    def remove_selected_joints(self):
        selected = self.joint_widget.selectedItems()
        if not selected:
            return
        for item in selected:
            name = item.text()
            self.joint_widget.takeItem(self.joint_widget.row(item))
            self.joint_list.remove(name)
        self.update_generate_button_state()

    def on_add_joints_button_pressed(self):
        dimmed_names = self.get_widget_joint_list()
        joint_picker = JointPickerWindow(
            parent=self,
            event_handler=self.event_handler,
            dimmed_names=dimmed_names,
            dimmed_tooltip='Joint names with dimmed color have already been added.')
        joint_picker.exec()
        if joint_picker.result() == QtWidgets.QDialog.Accepted:
            if joint_picker.get_picked_joint_list():
                if not self.joint_list:
                    self.joint_list = joint_picker.get_picked_joint_list()
                else:
                    self.joint_list.extend(joint_picker.get_picked_joint_list())
                    self.joint_list = list(dict.fromkeys(self.joint_list))  # Remove duplicates.
            self.set_joint_list(self.joint_list)

    def on_fbx_folder_changed(self, folder_name: str):
        self.update_generate_button_state()

    def set_joint_list(self, joints: list):
        self.joint_widget.clear()
        if not joints:
            self.joint_list = list()
            self.update_generate_button_state()
            return

        self.joint_list = joints
        if len(self.filter_text) > 0:
            for joint in joints:
                if self.filter_text.lower() in joint.lower():
                    self.joint_widget.addItem(joint)
        else:
            for joint in joints:
                self.joint_widget.addItem(joint)

        self.update_generate_button_state()

    def on_joint_widget_context_menu(self, point):
        selected_items = self.joint_widget.selectedItems()

        menu = QtWidgets.QMenu(self)
        add_action = menu.addAction('Add Joints')
        remove_selected_action = menu.addAction('Remove Selected Joints') if len(selected_items) > 0 else None
        menu.addSeparator()
        clear_action = menu.addAction('Clear') if self.joint_widget.count() > 0 else None

        action = menu.exec_(self.mapToGlobal(point))
        if action:
            if clear_action and action == clear_action:
                self.clear_joint_list()
            elif action == add_action:
                self.on_add_joints_button_pressed()
            elif remove_selected_action and action == remove_selected_action:
                self.remove_selected_joints()

    def get_widget_joint_list(self):
        if self.joint_widget.count():
            items = [self.joint_widget.item(i) for i in range(self.joint_widget.count())]
            return [item.text() for item in items]
        else:
            return None

    def clear_joint_list(self):
        self.set_joint_list(list())
