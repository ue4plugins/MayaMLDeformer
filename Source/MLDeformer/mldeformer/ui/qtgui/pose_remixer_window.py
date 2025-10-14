# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

import os
import json

from mldeformer.ui.Qt import QtCore, QtGui, QtWidgets
from mldeformer.ui.qtgui.joint_picker_window import JointPickerWindow
from mldeformer.ui.recent_file_list import RecentFileList

import mldeformer.optional_numpy


class PoseRemixerJsonEncoder(json.JSONEncoder):
    def default(self, object):
        if isinstance(object, PoseRemixerConfig):
            return object.__dict__
        if isinstance(object, JointGroup):
            return object.__dict__
        else:
            return json.JSONEncoder.default(self, object)


class PoseRemixerConfig:
    def __init__(self):
        self.group_list = list()

    def load_from_file(self, path: str):
        with open(path, 'rt') as readFile:
            json_string = readFile.readlines()
            if len(json_string) > 0:
                json_string = ' '.join(json_string)  # Turn the list of strings into one string.
                data = json.loads(json_string)
                self.init_from_json_data(data)

    def save_to_file(self, path: str):
        json_string = json.dumps(self, sort_keys=True, indent=4, cls=PoseRemixerJsonEncoder)
        with open(path, 'wt') as writeFile:
            writeFile.writelines(json_string)

    def init_from_json_data(self, config_data):
        if 'group_list' in config_data:
            self.group_list = list()
            for group in config_data['group_list']:
                name = group['name'] if 'name' in group else ''
                is_enabled = group['is_enabled'] if 'is_enabled' in group else True
                joint_list = list()
                if 'joint_list' in group:
                    for joint_name in group['joint_list']:
                        joint_list.append(joint_name)

                new_group = JointGroup(joint_list=joint_list, group_name=name, is_enabled=is_enabled)
                self.group_list.append(new_group)


class CustomItemDelegate(QtWidgets.QStyledItemDelegate):
    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setHeight(18)
        return size


class JointGroup:
    def __init__(self, joint_list: list = None, group_name: str = '', is_enabled: bool = True):
        self.joint_list = joint_list if joint_list is not None else list()
        self.is_enabled = is_enabled
        self.name = group_name


class PoseRemixerWindow(QtWidgets.QMainWindow):
    main_button_size = 22
    group_enabled_color = QtGui.QColor(255, 255, 255)
    group_disabled_color = QtGui.QColor(100, 100, 100)
    joint_does_not_exists_color = QtGui.QColor(255, 100, 100)
    joint_is_duplicate_color = QtGui.QColor(255, 200, 100)

    def __init__(self, event_handler):
        super(PoseRemixerWindow, self).__init__(event_handler.get_parent_window())

        self.config = PoseRemixerConfig()
        self.recent_configs_menu = None
        self.group_list = list()

        self.main_widget = None
        self.main_layout = None
        self.generate_button = None
        self.add_group_button = None
        self.header_layout = None
        self.group_widget = None
        self.event_handler = event_handler

        self.recent_config_list_file = os.path.join(self.event_handler.rig_deformer_path, 'RecentPoseRemixer.configList')
        self.recent_config_list = RecentFileList()
        self.recent_config_list.load(self.recent_config_list_file)

        self.bold_font = QtGui.QFont()
        self.bold_font.setBold(True)

        self.init_ui()

    def init_ui(self):
        print('[MLDeformer] Creating Pose Remixer UI')

        # Create the main window.
        self.setObjectName('MLDeformerPoseRemixerWindow')
        self.setWindowTitle('ML Deformer (Unreal Engine) - Pose Remixer Tool')
        self.setWindowIcon(QtGui.QIcon(self.event_handler.unreal_icon_path))
        self.resize(600, 800)

        self.create_main_menu()

        # Create the main widget and layout.
        self.main_widget = QtWidgets.QWidget()
        self.main_layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.setCentralWidget(self.main_widget)

        # Create the horizontal layout for buttons, above the listbox.
        self.header_layout = QtWidgets.QHBoxLayout()
        self.main_layout.addLayout(self.header_layout)

        # Create the joint group text item.
        list_label = QtWidgets.QLabel('Joint Groups:')
        list_label.setStyleSheet('color: orange')
        self.header_layout.addWidget(list_label)

        # Add a filler.
        filler_widget = QtWidgets.QWidget()
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        filler_widget.setSizePolicy(size_policy)
        self.header_layout.addWidget(filler_widget)

        # Create the add button.
        self.add_group_button = QtWidgets.QPushButton(QtGui.QIcon(self.event_handler.add_icon_path), '')
        self.add_group_button.setStyleSheet('background-color: green')
        self.add_group_button.setFixedSize(self.main_button_size, self.main_button_size)
        self.add_group_button.clicked.connect(self.on_add_group_button_pressed)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.add_group_button.setSizePolicy(size_policy)
        self.add_group_button.setToolTip('Add a new joint group to the list.')
        self.header_layout.addWidget(self.add_group_button)

        # Add the group tree view.
        self.group_widget = QtWidgets.QTreeWidget()
        self.group_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.group_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.group_widget.customContextMenuRequested.connect(self.on_group_widget_context_menu)
        self.group_widget.setHeaderLabels(['Name'])
        self.group_widget.setItemDelegate(CustomItemDelegate(self.group_widget))

        self.main_layout.addWidget(self.group_widget)

        if not mldeformer.optional_numpy.numpy_supported():
            numpy_message_widget = QtWidgets.QLabel(
                'Error: This tool requires NumPy. Generate button permanently disabled.')
            numpy_message_widget.setStyleSheet('color: rgb(255, 100, 100)')
            self.main_layout.addWidget(numpy_message_widget)

        # Add the generate button.
        self.generate_button = QtWidgets.QPushButton('Generate Animation')
        self.generate_button.clicked.connect(self.on_generate_button_pressed)
        self.main_layout.addWidget(self.generate_button)

        # self.set_group_list(groups)
        self.group_widget.expandAll()
        self.group_widget.itemChanged.connect(self.on_group_widget_item_changed)
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
            filter='Configuration Files (*.poseRemixerConfig)')

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
            filter='Configuration Files (*.poseRemixerConfig)')

        if len(file_path) > 0:
            self.load_config_file(file_path)

    def update_config(self):
        self.config.group_list = self.group_list

    def on_reset_config(self):
        response = QtWidgets.QMessageBox.question(self, 'Clear All?', 'This will delete all groups.\nDo you wish to continue?',
                                                  QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                  QtWidgets.QMessageBox.No)
        if response == QtWidgets.QMessageBox.Yes:
            self.config = PoseRemixerConfig()
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
        self.set_group_list(self.config.group_list)
        self.group_widget.expandAll()

    def update_generate_button_state(self):
        if not mldeformer.optional_numpy.numpy_supported():
            self.generate_button.setEnabled(False)
            return

        groups = self.generate_group_list_for_remix()
        is_enabled = len(groups) > 0
        self.generate_button.setEnabled(is_enabled)

    def generate_group_list_for_remix(self) -> list:
        groups = list()
        joint_names_in_scene = list(self.event_handler.get_joint_names().keys())
        for group in self.group_list:
            if group.is_enabled and group.joint_list:
                # Get the joints that are in the list, and exist in the scene
                joint_list = list(set(group.joint_list) & set(joint_names_in_scene))
                if joint_list:
                    groups.append(joint_list)

        return groups

    def on_generate_button_pressed(self):
        print('Generate Animation button pressed')
        groups = self.generate_group_list_for_remix()
        if not groups:
            print('There are no valid groups, with existing joints inside them.')
            return

            # Execute the remixing.
        self.event_handler.execute_pose_remixing(joint_groups=groups)

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Delete:
            widget = QtWidgets.QApplication.focusWidget()
            if widget == self.group_widget:
                self.remove_selected_items()

    def remove_selected_items(self):
        selected = self.group_widget.selectedItems()
        if not selected:
            return

        for item in selected:
            group = item.data(0, QtCore.Qt.UserRole)
            assert group is not None

            # if we are dealing with a joint.
            if item.parent() is not None:
                joint_name = item.text(0)
                index = group.joint_list.index(joint_name)
                del group.joint_list[index]
                item.parent().removeChild(item)
                del item
            else:  # We are dealing with a group.
                # First delete all joints in the group, then delete the actual group.
                group.joint_list = list()
                index = self.group_widget.indexOfTopLevelItem(item)
                self.group_widget.takeTopLevelItem(index)
                del item
                self.group_list.remove(group)

        self.update_joint_item_colors()
        self.update_generate_button_state()

    def on_add_group_button_pressed(self):
        self.create_new_group()

    @staticmethod
    def add_joint_widget_item(group_item: QtWidgets.QTreeWidgetItem, joint_name: str):
        item = QtWidgets.QTreeWidgetItem(group_item, [joint_name])
        joint_group = group_item.data(0, QtCore.Qt.UserRole)
        item.setData(0, QtCore.Qt.UserRole, joint_group)

    def add_group_widget_item(self, group: JointGroup) -> QtWidgets.QTreeWidgetItem:
        group_name = 'Group' if not group.name else group.name
        group.name = group_name
        group_root_color = PoseRemixerWindow.group_enabled_color if group.is_enabled else PoseRemixerWindow.group_disabled_color
        group_root = QtWidgets.QTreeWidgetItem(self.group_widget, [group_name])
        group_root.setForeground(0, group_root_color)
        group_root.setFont(0, self.bold_font)
        group_root.setFlags(group_root.flags() | QtCore.Qt.ItemIsEditable)
        group_root.setData(0, QtCore.Qt.UserRole, group)
        return group_root

    def set_group_list(self, groups: list):
        self.group_widget.clear()
        if not groups:
            self.group_list = list()
            self.update_generate_button_state()
            return

        self.group_list = groups
        self.group_widget.blockSignals(True)

        for group_index, joint_group in enumerate(groups):
            group_root = self.add_group_widget_item(group=joint_group)
            for joint_name in joint_group.joint_list:
                PoseRemixerWindow.add_joint_widget_item(group_item=group_root, joint_name=joint_name)

        self.update_joint_item_colors()
        self.group_widget.blockSignals(False)
        self.update_generate_button_state()

    def on_group_widget_context_menu(self, point):
        selected_items = self.group_widget.selectedItems()

        menu = QtWidgets.QMenu(self)
        create_group_action = menu.addAction('Create Group')

        add_joints_action = None
        rename_group_action = None
        enable_disable_action = None
        if len(selected_items) == 1:
            if selected_items[0].parent() is None:
                menu.addSeparator()
                add_joints_action = menu.addAction('Add Joints to Group')
                menu.addSeparator()
                rename_group_action = menu.addAction('Rename')
                is_enabled = selected_items[0].data(0, QtCore.Qt.UserRole).is_enabled
                enable_disable_action = menu.addAction('Disable Group') if is_enabled else menu.addAction('Enable Group')

        remove_selected_action = None
        clear_all_action = None
        if len(selected_items) > 0:
            menu.addSeparator()
            remove_selected_action = menu.addAction('Remove Selected Items')
            menu.addSeparator()
            clear_all_action = menu.addAction('Clear All')

        action = menu.exec_(self.mapToGlobal(point))
        if action:
            if create_group_action and action == create_group_action:
                self.create_new_group()
            elif add_joints_action and action == add_joints_action:
                self.add_joints_to_group(selected_items[0])
            elif remove_selected_action and action == remove_selected_action:
                self.remove_selected_items()
            elif clear_all_action and action == clear_all_action:
                response = QtWidgets.QMessageBox.question(self, 'Clear All?', 'This will delete all groups.\nDo you wish to continue?',
                                                          QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                          QtWidgets.QMessageBox.No)
                if response == QtWidgets.QMessageBox.Yes:
                    self.clear_group_list()
            elif rename_group_action and action == rename_group_action:
                self.group_widget.editItem(selected_items[0], 0)
            elif enable_disable_action and action == enable_disable_action:
                group = selected_items[0].data(0, QtCore.Qt.UserRole)
                group.is_enabled = not group.is_enabled
                self.set_group_list(self.group_list)
                self.group_widget.expandAll()

    def get_widget_joint_list(self):
        joint_list = list()
        for group in self.group_list:
            joint_list.extend(group.joint_list)
        joint_list = list(set(joint_list))  # Remove duplicates.
        return joint_list

    def clear_group_list(self):
        self.set_group_list(list())

    @staticmethod
    def on_group_widget_item_changed(item, column):
        if column == 0:
            new_name = item.text(column)
            joint_group = item.data(0, QtCore.Qt.UserRole)
            joint_group.name = new_name

    def create_new_group(self):
        self.group_widget.blockSignals(True)
        new_group = JointGroup()
        self.group_list.append(new_group)
        group_item = self.add_group_widget_item(group=new_group)
        if not self.add_joints_to_group(group_item=group_item):
            index = self.group_widget.indexOfTopLevelItem(group_item)
            self.group_widget.takeTopLevelItem(index)
            del group_item
            index = self.group_list.index(new_group)
            del self.group_list[index]
        else:
            group_item.setExpanded(True)
        self.group_widget.blockSignals(False)
        self.update_generate_button_state()

    def add_joints_to_group(self, group_item: QtWidgets.QTreeWidgetItem) -> bool:
        dimmed_names = self.get_widget_joint_list()
        joint_picker = JointPickerWindow(
            parent=self,
            event_handler=self.event_handler,
            dimmed_names=dimmed_names,
            dimmed_tooltip='Joint names with dimmed color have already been added to some group.')
        joint_picker.exec()
        if joint_picker.result() == QtWidgets.QDialog.Accepted:
            group = group_item.data(0, QtCore.Qt.UserRole)
            picked_joints = joint_picker.get_picked_joint_list()
            if picked_joints:
                new_joints = list(set(picked_joints) - set(group.joint_list))
                group.joint_list.extend(new_joints)
                for joint_name in new_joints:
                    PoseRemixerWindow.add_joint_widget_item(group_item=group_item, joint_name=joint_name)

                self.update_joint_item_colors()
                self.update_generate_button_state()
                return True
            else:
                return False
        else:
            return False

    def joint_exists_in_multiple_enabled_groups(self, joint_name: str) -> bool:
        num_occurrences = 0
        for group in self.group_list:
            if not group.is_enabled:
                continue
                
            if joint_name in group.joint_list:
                num_occurrences += 1
                if num_occurrences > 1:
                    return True
        return False

    def update_joint_item_colors(self):
        # Get the list of joints in the dcc scene.
        dcc_joints = list(self.event_handler.get_joint_names().keys())

        # Iterate over all groups, and all joints inside the groups.
        # Then color each joint item, based on whether there are duplicates, if the joint exists in the dcc scene or not, etc.
        root = self.group_widget.invisibleRootItem()
        num_groups = root.childCount()
        for group_index in range(num_groups):
            group_item = root.child(group_index)
            num_joints = group_item.childCount()
            for joint_index in range(num_joints):
                joint_item = group_item.child(joint_index)
                joint_name = joint_item.text(0)
                group = group_item.data(0, QtCore.Qt.UserRole)
                if group.is_enabled:
                    if joint_name in dcc_joints:
                        if self.joint_exists_in_multiple_enabled_groups(joint_name=joint_name):
                            joint_item.setForeground(0, PoseRemixerWindow.joint_is_duplicate_color)
                            joint_item.setToolTip(0, 'Warning: The joint exists in multiple groups.')
                        else:  # There are no issues, reset the foreground color to the default foreground color.
                            joint_item.setData(0, QtCore.Qt.ForegroundRole, None)
                            joint_item.setToolTip(0, '')
                    else:  # Joint doesn't exist in the scene.
                        joint_item.setForeground(0, PoseRemixerWindow.joint_does_not_exists_color)
                        joint_item.setToolTip(0, 'Error: This joint does not exist inside the scene. Joint will be ignored.')
                else:  # The group is disabled.
                    joint_item.setForeground(0, PoseRemixerWindow.group_disabled_color)
                    joint_item.setToolTip(0, 'The joint is inside a disabled group. Disabled groups will act like they do not exist.')
