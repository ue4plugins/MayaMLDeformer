# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

import json
import os
from re import search

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

from mldeformer.ui.parameter import Parameter
from mldeformer.ui.parameter_filter import ParameterFilter
from mldeformer.ui.event_handler import EventHandler
from mldeformer.ui.qtgui.editable_list_widget import EditableListWidget
from mldeformer.ui.qtgui.filter_widget import FilterWidget
from mldeformer.ui.qtgui.helpers import QtHelpers
from mldeformer.ui.recent_file_list import RecentFileList


class addParametersWindow(QtWidgets.QMainWindow):
    add_button_pressed = QtCore.Signal()

    # Some constants.
    table_column__name = 0
    table_column__default = 1
    table_column__minimum = 2
    table_column__maximum = 3
    table_column__object_type = 4
    table_column__group_name = 5

    min_label_text_width = 120
    main_button_size = 22

    def __init__(self, parent, event_handler):
        super(addParametersWindow, self).__init__(parent)

        self.parameter_list = list()
        self.filter = ParameterFilter()
        self.event_handler = event_handler
        self.selected_attribute = ''
        self.filter_text = ''
        self.recent_filter_settings = RecentFileList()
        self.recent_filter_settings_file = os.path.join(self.event_handler.rig_deformer_path, 'Recent.filterList')

        # Load last filter settings.
        # Register defaults when the file doesn't exist or failed to load= for some reason.
        if not self.load_filter_settings(file_to_load=self.event_handler.last_filter_settings_file,
                                         update_recent_file_list=False,
                                         update_ui=False):
            self.event_handler.register_default_filter_settings(self.filter)

        # Create the main window.
        self.setObjectName('MLRigGeneratoraddParametersWindow')
        self.setWindowTitle('Add Parameters')
        self.resize(1100, 600)
        self.main_widget = QtWidgets.QWidget(self)
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

        # ----------------------------------------------------------
        # Create the left side contents widget.
        self.left_widget = QtWidgets.QWidget(self)
        self.left_layout = QtWidgets.QVBoxLayout(self.left_widget)

        # Create the parameters label bar.
        parameters_layout = QtWidgets.QHBoxLayout()
        self.left_layout.addLayout(parameters_layout)
        self.parameters_label = QtWidgets.QLabel('Resulting Attributes')
        self.parameters_label.setStyleSheet('color: orange')
        parameters_layout.addWidget(self.parameters_label)
        filler_widget = QtWidgets.QWidget()
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        filler_widget.setSizePolicy(size_policy)
        parameters_layout.addWidget(filler_widget)

        self.filter_widget = FilterWidget(self.main_button_size)
        self.filter_widget.text_changed.connect(self.on_filter_text_changed)
        parameters_layout.addWidget(self.filter_widget)

        self.refresh_parameters_button = QtWidgets.QPushButton(QtGui.QIcon(self.event_handler.refresh_icon_path), '')
        self.refresh_parameters_button.setFixedSize(self.main_button_size, self.main_button_size)
        self.refresh_parameters_button.clicked.connect(self.init_parameters_table)
        self.refresh_parameters_button.setToolTip(
            'Refresh the attribute list.\nPress this after you change selection inside Maya.')
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.refresh_parameters_button.setSizePolicy(size_policy)
        parameters_layout.addWidget(self.refresh_parameters_button)

        # Create the parameters table.
        self.parameters_table = QtWidgets.QTableWidget(0, 5)
        self.parameters_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.parameters_table.customContextMenuRequested.connect(self.on_table_context_menu)
        self.parameters_table.itemSelectionChanged.connect(self.on_table_selection_changed)
        self.left_layout.addWidget(self.parameters_table)
        self.parameters_table.setHorizontalHeaderLabels(['Parameter Name', 'Default', 'Min', 'Max', 'Object Type'])
        self.parameters_table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.parameters_table.verticalHeader().setVisible(False)
        self.parameters_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.parameters_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        for col in range(self.parameters_table.columnCount()):
            self.parameters_table.horizontalHeader().setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeToContents)

        table_width = self.parameters_table.geometry().width()
        self.parameters_table.setColumnWidth(self.table_column__name, table_width * 0.5)
        self.parameters_table.setColumnWidth(self.table_column__default, table_width * 0.1)
        self.parameters_table.setColumnWidth(self.table_column__minimum, table_width * 0.1)
        self.parameters_table.setColumnWidth(self.table_column__maximum, table_width * 0.1)
        self.parameters_table.setColumnWidth(self.table_column__object_type, table_width * 0.2)
        self.parameters_table.setColumnWidth(self.table_column__group_name, table_width * 0.2)
        
        self.parameters_table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
        self.parameters_table.horizontalHeader().setStretchLastSection(True)
        self.parameters_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)

        # Create the right side of the UI.
        self.right_widget = QtWidgets.QWidget()
        self.right_layout = QtWidgets.QVBoxLayout(self.right_widget)

        # Create the hierarchy properties group.
        self.hierarchy_properties_group = QtWidgets.QGroupBox('Hierarchy Filter')
        self.hierarchy_properties_group.setStyleSheet('QGroupBox::title { color: orange }')
        self.right_layout.addWidget(self.hierarchy_properties_group)
        self.hierarchy_filter_grid_layout = QtWidgets.QGridLayout()
        self.hierarchy_filter_grid_layout.setColumnStretch(0, 0)
        self.hierarchy_filter_grid_layout.setColumnStretch(1, 1)

        _, self.object_filter_combo_box = QtHelpers.add_combo_box_field(layout=self.hierarchy_filter_grid_layout,
                                                                        row_index=0,
                                                                        name='Filter Mode:',
                                                                        combo_items=['All Object Types',
                                                                                     'Specified Object Types'],
                                                                        min_label_text_width=self.min_label_text_width)
        self.include_joints_label, self.include_joints_check_box = QtHelpers.add_check_box_field(
            layout=self.hierarchy_filter_grid_layout, row_index=1, name='Include Joints:',
            value=self.filter.include_joints,
            min_label_text_width=self.min_label_text_width)
        self.include_transforms_label, self.include_transforms_check_box = QtHelpers.add_check_box_field(
            layout=self.hierarchy_filter_grid_layout, row_index=2, name='Include Transforms:',
            value=self.filter.include_transforms, min_label_text_width=self.min_label_text_width)
        self.include_shapes_label, self.include_shapes_check_box = QtHelpers.add_check_box_field(
            layout=self.hierarchy_filter_grid_layout, row_index=3, name='Include Shapes:',
            value=self.filter.include_shapes,
            min_label_text_width=self.min_label_text_width)
        _, self.include_children_check_box = QtHelpers.add_check_box_field(layout=self.hierarchy_filter_grid_layout,
                                                                           row_index=4,
                                                                           name='Include Children:',
                                                                           value=self.filter.include_children,
                                                                           min_label_text_width=self.min_label_text_width)

        self.object_filter_combo_box.currentIndexChanged.connect(self.init_parameters_table)
        self.include_joints_check_box.stateChanged.connect(self.init_parameters_table)
        self.include_transforms_check_box.stateChanged.connect(self.init_parameters_table)
        self.include_shapes_check_box.stateChanged.connect(self.init_parameters_table)
        self.include_children_check_box.stateChanged.connect(self.init_parameters_table)

        # Add the object type include list widget.
        self.object_type_include_list_widget = EditableListWidget(self.event_handler)
        self.object_type_include_list_widget.default_new_item_string = '<object type name>'
        self.object_type_include_list_widget.set_contents(self.filter.include_custom_types)
        self.object_type_include_list_widget.list_widget.contents_changed.connect(self.init_parameters_table)
        self.include_custom_label, _ = QtHelpers.add_widget_field(layout=self.hierarchy_filter_grid_layout, row_index=6,
                                                                  name='Include Types:',
                                                                  widget=self.object_type_include_list_widget,
                                                                  min_label_text_width=self.min_label_text_width)

        # Add the object type ignore list widget.
        self.object_type_ignore_list_widget = EditableListWidget(self.event_handler)
        self.object_type_ignore_list_widget.default_new_item_string = '<object type name>'
        self.object_type_ignore_list_widget.set_contents(self.filter.exclude_custom_types)
        self.object_type_ignore_list_widget.list_widget.contents_changed.connect(self.init_parameters_table)
        self.exclude_custom_label, _ = QtHelpers.add_widget_field(layout=self.hierarchy_filter_grid_layout, row_index=7,
                                                                  name='Ignore Types:',
                                                                  widget=self.object_type_ignore_list_widget,
                                                                  min_label_text_width=self.min_label_text_width)

        self.object_filter_combo_box.setToolTip(
            'Should we include all objects, or allow filtering of specific object types?')
        self.include_joints_check_box.setToolTip('Include all objects that are joints?')
        self.include_transforms_check_box.setToolTip('Include all objects that are transforms?')
        self.include_shapes_check_box.setToolTip('Include all shapes?')
        self.include_children_check_box.setToolTip('Include all children and grand children of the selected objects?')
        self.object_type_include_list_widget.setToolTip(
            'additionally include objects that are of the type specified.\n\nExample:\nmesh, ikEffector, aimConstraint')
        self.object_type_ignore_list_widget.setToolTip(
            'A list of object types that should be ignored.\n\nExample:\nmesh, ikEffector, aimConstraint')

        # self.right_layout.addWidget(self.hierarchy_properties_group)
        self.hierarchy_properties_group.setLayout(self.hierarchy_filter_grid_layout)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.hierarchy_properties_group.setSizePolicy(size_policy)

        # Create the attributes filter group.
        self.attributes_properties_group = QtWidgets.QGroupBox('Attributes Filter')
        self.attributes_properties_group.setStyleSheet('QGroupBox::title { color: orange }')
        self.right_layout.addWidget(self.attributes_properties_group)
        self.attributes_filter_grid_layout = QtWidgets.QGridLayout()
        self.attributes_filter_grid_layout.setColumnStretch(0, 0)
        self.attributes_filter_grid_layout.setColumnStretch(1, 1)

        _, self.attributes_combo_box = QtHelpers.add_combo_box_field(layout=self.attributes_filter_grid_layout,
                                                                     row_index=0,
                                                                     name='Attributes:',
                                                                     combo_items=['All Keyable',
                                                                                  'Selected in ChannelBox'],
                                                                     min_label_text_width=self.min_label_text_width)
        self.attributes_combo_box.currentIndexChanged.connect(self.init_parameters_table)

        # Add the attribute ignore list widget.
        self.attribute_ignore_list_widget = EditableListWidget(self.event_handler)
        self.attribute_ignore_list_widget.default_new_item_string = '<attribute name>'
        self.attribute_ignore_list_widget.set_contents(self.filter.exclude_attributes)
        self.attribute_ignore_list_widget.list_widget.contents_changed.connect(self.init_parameters_table)
        QtHelpers.add_widget_field(layout=self.attributes_filter_grid_layout, row_index=1, name='Ignore List:',
                                   widget=self.attribute_ignore_list_widget,
                                   min_label_text_width=self.min_label_text_width)

        self.attribute_ignore_list_widget.setToolTip(
            'Attributes to ignore.\n\nExample:\nvisibility, translateX, scaleY')

        self.attributes_properties_group.setLayout(self.attributes_filter_grid_layout)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.attributes_properties_group.setSizePolicy(size_policy)

        self.object_filter_combo_box.blockSignals(True)
        self.object_filter_combo_box.currentIndexChanged.connect(self.on_filter_mode_changed)
        self.object_filter_combo_box.setCurrentIndex(0 if self.filter.include_all else 1)

        self.attributes_combo_box.blockSignals(True)
        self.attributes_combo_box.setCurrentIndex(1 if self.filter.selected_channels_only else 0)

        self.attributes_combo_box.blockSignals(False)
        self.object_filter_combo_box.blockSignals(False)

        # Add a filler to fill the bottom of the right side.
        filler_widget = QtWidgets.QWidget()
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)
        filler_widget.setSizePolicy(size_policy)
        self.right_layout.addWidget(filler_widget)

        # Add the 'Add Parameters' button.
        self.add_buttons_layout = QtWidgets.QHBoxLayout()

        self.add_selected_parameters_button = QtWidgets.QPushButton('Add Selected Parameters')
        self.add_selected_parameters_button.clicked.connect(self.on_add_selected_parameters_button_pressed)
        self.add_selected_parameters_button.setEnabled(False)
        self.add_buttons_layout.addWidget(self.add_selected_parameters_button)

        self.add_parameters_button = QtWidgets.QPushButton('Add All Parameters')
        self.add_parameters_button.clicked.connect(self.on_add_parameters_button_pressed)
        self.add_buttons_layout.addWidget(self.add_parameters_button)

        self.right_layout.addLayout(self.add_buttons_layout)

        # Create the splitter.
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)
        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.right_widget)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        self.splitter.setSizes([800, 200])

        # Add the parameters to the table.
        self.init_parameters_table()

        self.parameters_table.clearSelection()

        self.recent_filter_settings.load(self.recent_filter_settings_file)
        self.create_main_menu()

        self.parameters_table.setColumnWidth(self.table_column__name, 400)

    # Resize the row heights to fit the contents nicely when we resize the window.
    def resizeEvent(self, event):
        QtWidgets.QMainWindow.resizeEvent(self, event)
        self.parameters_table.resizeRowsToContents()

    # Prevents keyboard press events from being passed onto the DCC.
    def keyPressEvent(self, event):
        pass

    # Create the main menu bar.
    def create_main_menu(self):
        self.main_menu = self.menuBar()
        self.file_menu = self.main_menu.addMenu('File')

        # Open a config file. 
        open_action = QtWidgets.QAction(QtGui.QIcon(self.event_handler.open_icon_path), 'Load filter settings', self)
        open_action.setShortcut('Ctrl+O')
        self.file_menu.addAction(open_action)
        open_action.triggered.connect(self.on_load_filter_settings)

        # save a config file.
        save_action = QtWidgets.QAction(QtGui.QIcon(self.event_handler.save_icon_path), 'Save filter settings', self)
        save_action.setShortcut('Ctrl+S')
        self.file_menu.addAction(save_action)
        save_action.triggered.connect(self.on_save_filter_settings)

        self.file_menu.addSeparator()

        self.recent_filters_menu = self.file_menu.addMenu('Recent Filters')
        self.fill_recent_filters_menu()

        # Edit menu.
        self.edit_menu = self.main_menu.addMenu('Edit')
        reset_filter_action = QtWidgets.QAction('Reset Filter', self)
        reset_filter_action.setShortcut('Ctrl+R')
        reset_filter_action.triggered.connect(self.on_reset_filter)
        self.edit_menu.addAction(reset_filter_action)

    def on_filter_text_changed(self, text):
        self.filter_text = text
        self.init_parameters_table()
        self.parameters_table.clearSelection()

    def on_reset_filter(self):
        self.filter = ParameterFilter()
        self.update_filter_settings_ui()

    def fill_recent_filters_menu(self):
        self.recent_filters_menu.clear()
        for item in reversed(self.recent_filter_settings.file_list):
            action = self.recent_filters_menu.addAction(item)
            action.triggered.connect(self.on_recent_filter_settings)

    def on_recent_filter_settings(self):
        action = self.sender()
        self.load_filter_settings(action.text(), True)

    def on_load_filter_settings(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption='Load filter settings...',
            dir=self.event_handler.rig_deformer_path,
            filter='Filter Settings Files (*.filterSettings)')

        if len(file_path) > 0:
            self.load_filter_settings(file_path, True)

    def load_filter_settings(self, file_to_load, update_recent_file_list, update_ui=True):
        json_string = ''
        try:
            with open(file_to_load, 'rt') as readFile:
                json_string = readFile.readlines()
                if len(json_string) > 0:
                    json_string = ' '.join(json_string)  # Turn the list of strings into one string.
                    data = json.loads(json_string)
                    self.filter.parse_filter_settings_json_data(data)
                    if update_recent_file_list:
                        self.recent_filter_settings.add(file_to_load)
                        self.fill_recent_filters_menu()
                    if update_ui:
                        self.update_filter_settings_ui()
        except Exception as e:
            print(str(e))
            return False
        return True

    def on_save_filter_settings(self):
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption='Save filter settings as...',
            dir=self.event_handler.rig_deformer_path,
            filter='Filter Settings Files (*.filterSettings)')

        if len(file_path) > 0:
            self.save_filter_settings(file_path, True)

    def save_filter_settings(self, file_to_save, update_recent_file_list):
        json_string = self.filter.to_json()
        try:
            with open(file_to_save, 'wt') as writeFile:
                writeFile.writelines(json_string)
                if update_recent_file_list:
                    if file_to_save not in self.recent_filter_settings.file_list:
                        self.recent_filter_settings.add(file_to_save)
                        self.recent_filter_settings.save(self.recent_filter_settings_file)
        except:
            print('[MLDeformer] Failed to write filter settings file')

    # Get a list of selected parameter indices.
    def get_selected_parameter_indices(self):
        resulting_indices = list()
        selected_items = self.parameters_table.selectedItems()
        col_count = self.parameters_table.columnCount()
        num_selected_rows = len(selected_items) / col_count
        assert (len(selected_items) % col_count) == 0, 'Expected entire row to be selected'
        for i in range(0, int(num_selected_rows)):
            item = selected_items[i * col_count + self.table_column__name]
            param_index = item.data(QtCore.Qt.UserRole)
            resulting_indices.append(param_index)
        return resulting_indices

    # Update the UI for the filter settings, based on the current filter settings.
    def update_filter_settings_ui(self):
        # Block widget signals, as they can trigger refreshes of the filter settings, which is what we should avoid.
        self.include_joints_check_box.blockSignals(True)
        self.include_transforms_check_box.blockSignals(True)
        self.include_shapes_check_box.blockSignals(True)
        self.include_children_check_box.blockSignals(True)
        self.attributes_combo_box.blockSignals(True)
        self.object_filter_combo_box.blockSignals(True)
        self.object_type_include_list_widget.blockSignals(True)
        self.object_type_ignore_list_widget.blockSignals(True)
        self.attribute_ignore_list_widget.blockSignals(True)

        self.include_joints_check_box.setChecked(self.filter.include_joints)
        self.include_transforms_check_box.setChecked(self.filter.include_transforms)
        self.include_shapes_check_box.setChecked(self.filter.include_shapes)
        self.include_children_check_box.setChecked(self.filter.include_children)

        self.attributes_combo_box.setCurrentIndex(1 if self.filter.selected_channels_only else 0)
        self.object_filter_combo_box.setCurrentIndex(0 if self.filter.include_all else 1)

        self.object_type_include_list_widget.set_contents(self.filter.include_custom_types)
        self.object_type_ignore_list_widget.set_contents(self.filter.exclude_custom_types)
        self.attribute_ignore_list_widget.set_contents(self.filter.exclude_attributes)

        # Disable blocking signals.
        self.include_joints_check_box.blockSignals(False)
        self.include_transforms_check_box.blockSignals(False)
        self.include_shapes_check_box.blockSignals(False)
        self.include_children_check_box.blockSignals(False)
        self.attributes_combo_box.blockSignals(False)
        self.object_filter_combo_box.blockSignals(False)
        self.object_type_include_list_widget.blockSignals(False)
        self.object_type_ignore_list_widget.blockSignals(False)
        self.attribute_ignore_list_widget.blockSignals(False)

        self.on_filter_mode_changed()
        self.init_parameters_table()

    def on_table_context_menu(self, point):
        items = self.parameters_table.selectedItems()
        if len(items) == 0:
            return

        menu = QtWidgets.QMenu(self)

        # Grab the selected attribute name.
        add_to_attribute_ignore_list_action = None
        attribute_name = ''
        if len(items) > 0:
            if len(items) == self.parameters_table.columnCount():
                attribute_name = items[self.table_column__name].text()
                split_values = items[self.table_column__name].text().split('.')
                if len(split_values) > 0:
                    attribute_name = split_values[-1]
                    add_to_attribute_ignore_list_action = menu.addAction(
                        str('Add attribute \'{}\' to ignore list').format(attribute_name))
            else:
                add_to_attribute_ignore_list_action = menu.addAction('Add selected attributes to ignore list')

        # Grab the object type.
        add_to_object_type_ignore_list_action = None
        add_to_object_type_include_list_action = None
        col_count = self.parameters_table.columnCount()
        num_selected_rows = len(items) / col_count
        unique_object_types = list()
        assert (len(items) % col_count) == 0, 'Expected entire row to be selected'
        object_type_list = list()
        for i in range(0, num_selected_rows):
            cur_item = items[i * col_count + self.table_column__object_type]
            object_type_list.append(cur_item.text())
        unique_object_types = list(set(object_type_list))  # Remove duplicates.

        if len(unique_object_types) == 1:
            object_type = unique_object_types[0]
            add_to_object_type_ignore_list_action = menu.addAction(
                str('Add object type \'{}\' to ignore list').format(object_type))
            menu.addSeparator()
            add_to_object_type_include_list_action = menu.addAction(
                str('Add object type \'{}\' to include list').format(object_type))
        else:
            assert len(unique_object_types) > 1, 'Expected multiple rows selected'
            add_to_object_type_ignore_list_action = menu.addAction('Add selected object types to ignore list')
            menu.addSeparator()
            add_to_object_type_include_list_action = menu.addAction('Add selected object types to include list')

        # Spawn the context menu and handle the action that was picked in the context menu.
        action = menu.exec_(self.mapToGlobal(point))
        if action:
            if add_to_attribute_ignore_list_action and action == add_to_attribute_ignore_list_action:  # Add selected attributes to ignore list.
                attribute_list = list()
                for i in range(0, num_selected_rows):
                    cur_item = items[i * col_count + self.table_column__name]
                    split_values = cur_item.text().split('.')
                    if len(split_values) > 0:
                        attribute_list.append(split_values[-1])
                unique_attributes = list(set(attribute_list))  # Remove duplicates.
                for attribute in unique_attributes:
                    if len(
                        self.attribute_ignore_list_widget.list_widget.findItems(attribute,
                                                                                QtCore.Qt.MatchExactly)) == 0:
                        self.attribute_ignore_list_widget.list_widget.add_item(attribute, trigger_contents_changed=False)
                self.attribute_ignore_list_widget.list_widget.emit_contents_changed()
            elif add_to_object_type_ignore_list_action and action == add_to_object_type_ignore_list_action:  # Add object type to ignore list.
                for object_type in unique_object_types:
                    if len(
                        self.object_type_ignore_list_widget.list_widget.findItems(object_type,
                                                                                  QtCore.Qt.MatchExactly)) == 0:
                        self.object_type_ignore_list_widget.list_widget.add_item(object_type, trigger_contents_changed=False)
                self.object_type_ignore_list_widget.list_widget.emit_contents_changed()
            elif add_to_object_type_include_list_action and action == add_to_object_type_include_list_action:  # Add object type to include list.
                for object_type in unique_object_types:
                    if len(
                        self.object_type_include_list_widget.list_widget.findItems(object_type,
                                                                                   QtCore.Qt.MatchExactly)) == 0:
                        self.object_type_include_list_widget.list_widget.add_item(object_type, trigger_contents_changed=False)
                self.object_type_include_list_widget.list_widget.emit_contents_changed()

        self.parameters_table.clearSelection()

    # When we press the add All button.
    def on_add_parameters_button_pressed(self):
        self.recent_filter_settings.save(self.recent_filter_settings_file)
        self.save_filter_settings(self.event_handler.last_filter_settings_file, False)
        self.add_button_pressed.emit()
        self.close()

    # When we press the add Selected button.
    def on_add_selected_parameters_button_pressed(self):
        selected_param_indices = self.get_selected_parameter_indices()

        # Update the parameter list with only the selected parameters.
        new_parameter_list = list()
        for param_index in selected_param_indices:
            param = self.parameter_list[param_index]
            new_param = Parameter()
            new_param.name = param.name
            new_param.display_name = param.display_name
            new_param.object_type = param.object_type
            new_param.min_value = param.min_value
            new_param.max_value = param.max_value
            new_param.default_value = param.default_value
            new_param.group_name = param.group_name
            new_parameter_list.append(new_param)

        self.parameter_list = new_parameter_list
        self.add_button_pressed.emit()
        self.close()

    def on_filter_mode_changed(self):
        include_all = (self.object_filter_combo_box.currentIndex() == 0)
        self.include_joints_check_box.setEnabled(not include_all)
        self.include_transforms_check_box.setEnabled(not include_all)
        self.object_type_include_list_widget.setEnabled(not include_all)
        self.include_shapes_check_box.setEnabled(not include_all)
        self.object_type_ignore_list_widget.setEnabled(include_all)
        self.include_joints_label.setEnabled(not include_all)
        self.include_transforms_label.setEnabled(not include_all)
        self.include_shapes_label.setEnabled(not include_all)
        self.include_custom_label.setEnabled(not include_all)
        self.exclude_custom_label.setEnabled(include_all)

    # When the selection changes in the table, extract which attribute was selected.
    # This can be used to automatically init the new attribute to add when pressing the + button in the ignore list.
    def on_table_selection_changed(self):
        items = self.parameters_table.selectedItems()
        if len(items) == 0:
            self.selected_attribute = ''
            self.add_selected_parameters_button.setEnabled(False)
            return

        self.selected_attribute = items[0].text()
        split_values = items[0].text().split('.')
        if len(split_values) > 0:
            self.selected_attribute = split_values[-1]

        if len(self.selected_attribute) == 0:
            self.selected_attribute = ''

        self.attribute_ignore_list_widget.newItemString = self.selected_attribute
        self.add_selected_parameters_button.setEnabled(True)

    def set_parameters_table_message(self, message):
        self.parameters_table.setColumnWidth(self.table_column__name, 800)
        self.parameters_table.setRowCount(1)
        name_item = QtWidgets.QTableWidgetItem(message)
        name_item.setData(QtCore.Qt.UserRole, 0)
        self.parameters_table.setItem(0, self.table_column__name, name_item)
        self.parameters_table.horizontalHeader().hide()
        self.parameters_table.clearSelection()
        self.parameters_table.setEnabled(False)
        self.parameters_table.setShowGrid(False)

    # Update the contents of the parameters table by clearing and refilling it.
    def init_parameters_table(self):
        self.filter = ParameterFilter()
        self.filter.include_children = self.include_children_check_box.isChecked()
        self.filter.include_all = (self.object_filter_combo_box.currentIndex() == 0)
        self.filter.include_transforms = self.include_transforms_check_box.isChecked()
        self.filter.include_joints = self.include_joints_check_box.isChecked()
        self.filter.include_shapes = self.include_shapes_check_box.isChecked()
        self.filter.selected_channels_only = (self.attributes_combo_box.currentIndex() == 1)

        self.filter.include_custom_types = list()
        for index in range(0, self.object_type_include_list_widget.list_widget.count()):
            item = self.object_type_include_list_widget.list_widget.item(index)
            self.filter.include_custom_types.append(item.text().lower())

        self.filter.exclude_custom_types = list()
        for index in range(0, self.object_type_ignore_list_widget.list_widget.count()):
            item = self.object_type_ignore_list_widget.list_widget.item(index)
            self.filter.exclude_custom_types.append(item.text().lower())

        self.filter.exclude_attributes = list()
        for index in range(0, self.attribute_ignore_list_widget.list_widget.count()):
            item = self.attribute_ignore_list_widget.list_widget.item(index)
            self.filter.exclude_attributes.append(item.text())

        self.parameter_list = self.event_handler.find_parameters(self.filter)

        # Remove filtered items.
        indices_to_remove = list()
        for index, parameter in enumerate(self.parameter_list):
            if len(self.filter_text) > 0:
                if not search(self.filter_text, parameter.display_name):
                    indices_to_remove.append(index)
        indices_to_remove = sorted(indices_to_remove, reverse=True)  # Remove last ones first.
        for index in indices_to_remove:
            del self.parameter_list[index]

        self.parameters_table.setRowCount(len(self.parameter_list))

        if len(self.parameter_list) == 0:
            self.filter.exclude_attributes = list()
            non_excluded_parameter_list = self.event_handler.find_parameters(self.filter)
            if non_excluded_parameter_list:
                self.set_parameters_table_message("All selected items have been filtered. Select different object and press refresh")
            else:
                self.set_parameters_table_message("Select joints / controls and press the refresh button")
            self.parameters_table.horizontalHeader().setStretchLastSection(True)
        else:
            self.parameters_table.setEnabled(True)
            self.parameters_table.setShowGrid(True)
            self.parameters_table.horizontalHeader().show()
        
        for row, parameter in enumerate(self.parameter_list):
            param_name_item = QtWidgets.QTableWidgetItem(parameter.display_name)
            param_name_item.setData(QtCore.Qt.UserRole, row)
            self.parameters_table.setItem(row, self.table_column__name, param_name_item)
            self.parameters_table.setItem(row, self.table_column__default,
                                          QtWidgets.QTableWidgetItem(str(parameter.default_value)))
            self.parameters_table.setItem(row, self.table_column__minimum,
                                          QtWidgets.QTableWidgetItem(str(parameter.min_value)))
            self.parameters_table.setItem(row, self.table_column__maximum,
                                          QtWidgets.QTableWidgetItem(str(parameter.max_value)))
            self.parameters_table.setItem(row, self.table_column__object_type,
                                          QtWidgets.QTableWidgetItem(parameter.object_type))
            self.parameters_table.setItem(row, self.table_column__group_name,
                                          QtWidgets.QTableWidgetItem(parameter.group_name))

        self.parameters_label.setText('Resulting Attributes ({})'.format(len(self.parameter_list)))
        self.parameters_table.resizeRowsToContents()
        self.parameters_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)

        self.add_parameters_button.setEnabled(len(self.parameter_list) > 0)

    def closeEvent(self, event):
        self.recent_filter_settings.save(self.recent_filter_settings_file)
        self.save_filter_settings(self.event_handler.last_filter_settings_file, False)
        self.deleteLater()
