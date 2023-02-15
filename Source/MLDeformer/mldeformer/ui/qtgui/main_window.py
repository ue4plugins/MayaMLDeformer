# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

import os
import time
from re import search

import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

from mldeformer.ui.config import Config
from mldeformer.ui.qtgui.add_parameters_window import addParametersWindow
from mldeformer.ui.qtgui.file_picker_field_widget import FilePickerFieldWidget
from mldeformer.ui.qtgui.filter_widget import FilterWidget
from mldeformer.ui.qtgui.helpers import QtHelpers
from mldeformer.ui.qtgui.mesh_mapping_widget import MeshMappingWidget
from mldeformer.ui.qtgui.param_minmax_setup_window import ParamMinMaxSetupWindow
from mldeformer.ui.recent_file_list import RecentFileList
from mldeformer.ui.qtgui.mesh_field_widget import MeshFieldWidget
from mldeformer.ui.qtgui.top_level_window import TopLevelWindow
from mldeformer.ui.qtgui.table_widget import TableWidget

class DeformerMainWindow(TopLevelWindow):
    # Some constants.
    table_column__name = 0
    table_column__default = 1
    table_column__minimum = 2
    table_column__maximum = 3
    table_column__object_type = 4
    table_column__group_name = 5

    min_label_text_width = 120
    main_button_size = 22

    def __init__(self, event_handler):
        super(DeformerMainWindow, self).__init__(event_handler)
        self.event_handler = event_handler

        self.setWindowIcon(QtGui.QIcon(self.event_handler.unreal_icon_path))

        self.red_brush = QtGui.QBrush(QtGui.QColor(255, 80, 0))
        self.dark_gray_brush = QtGui.QBrush(QtGui.QColor(95, 95, 95))
        self.table_default_foreground_brush = QtGui.QBrush(QtGui.QColor(200, 200, 200))

        self.filter_text = ''
        if self.event_handler.global_settings.auto_load_last_config:
            self.load_config_file(self.event_handler.last_config_file, init_ui=False, update_recent_file_list=False)

        self.recent_config_list_file = os.path.join(self.event_handler.rig_deformer_path, 'Recent.configList')
        self.recent_config_list = RecentFileList()
        self.recent_config_list.load(self.recent_config_list_file)

        self.init_ui()

        if self.event_handler.global_settings.auto_load_last_config:
            self.parameters_table.clearSelection()
            self.select_default_row()
            self.parameters_table.horizontalHeader().setStretchLastSection(True)
            self.parameters_table.setFocus()

    def select_default_row(self):
        len_config_params = len(self.event_handler.generator_config.parameters)
        if self.parameters_table.rowCount() > 0 and len_config_params > 0:
            self.parameters_table.selectRow(0)

    def closeEvent(self, event):
        self.event_handler.global_settings.save_to_file(self.event_handler.global_settings_file)
        self.event_handler.generator_config.save_to_file(self.event_handler.last_config_file)
        print('[MLDeformer] Closing main window')
        self.deleteLater()

    # Initialize the main UI.
    def init_ui(self):
        print('[MLDeformer] Creating UI')

        # Create the main window.
        self.setObjectName('MLDeformerGeneratorWindow')
        self.setWindowTitle('MLDeformer (Unreal Engine) - Training Data Generation Setup')
        self.resize(1150, 600)
        self.main_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.main_widget.setContentsMargins(0, 0, 0, 0)
        self.main_layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.create_main_menu()

        # ----------------------------------------------------------
        # Create the left side contents widget.
        self.left_widget = QtWidgets.QWidget(self.main_widget)
        self.left_layout = QtWidgets.QVBoxLayout(self.left_widget)

        # Create the parameters label bar.
        parameters_layout = QtWidgets.QHBoxLayout()
        self.left_layout.addLayout(parameters_layout)
        self.parameters_label = QtWidgets.QLabel('Parameters')
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
        self.refresh_parameters_button.clicked.connect(self.update)
        self.refresh_parameters_button.setToolTip(
            'Refresh the parameter list.\nPress this after you change selection inside or when you modified the scene.')
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.refresh_parameters_button.setSizePolicy(size_policy)
        parameters_layout.addWidget(self.refresh_parameters_button)

        self.add_parameter_button = QtWidgets.QPushButton(QtGui.QIcon(self.event_handler.add_icon_path), '')
        self.add_parameter_button.setStyleSheet('background-color: green')
        self.add_parameter_button.setFixedSize(self.main_button_size, self.main_button_size)
        self.add_parameter_button.clicked.connect(self.on_add_parameters_button_pressed)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.add_parameter_button.setSizePolicy(size_policy)
        parameters_layout.addWidget(self.add_parameter_button)

        # Create the main message.
        self.main_message = QtWidgets.QLabel('To start generation add parameters to sample using the green + button.'
                                             '\nMake sure you have at least one object selected in the outliner.')
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.main_message.setSizePolicy(size_policy)
        self.main_message.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.main_message.setStyleSheet('background-color: rgb(40, 40, 40)')
        self.left_layout.addWidget(self.main_message)

        # Create the parameters table.
        self.parameters_table = TableWidget(0, 6)
        self.parameters_table.hide()
        self.parameters_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.parameters_table.customContextMenuRequested.connect(self.on_table_context_menu)
        self.left_layout.addWidget(self.parameters_table)
        self.parameters_table.setHorizontalHeaderLabels(
            ['Parameter Name', 'Default', 'Min', 'Max', 'Object Type', 'Group'])
        self.parameters_table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.parameters_table.verticalHeader().setVisible(False)
        self.parameters_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.parameters_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        for col in range(self.parameters_table.columnCount()):
            self.parameters_table.horizontalHeader().setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeToContents)

        table_width = self.parameters_table.geometry().width()
        self.parameters_table.setColumnWidth(self.table_column__name, table_width * 0.4)
        self.parameters_table.setColumnWidth(self.table_column__default, table_width * 0.1)
        self.parameters_table.setColumnWidth(self.table_column__minimum, table_width * 0.1)
        self.parameters_table.setColumnWidth(self.table_column__maximum, table_width * 0.1)
        self.parameters_table.setColumnWidth(self.table_column__object_type, table_width * 0.15)
        self.parameters_table.setColumnWidth(self.table_column__group_name, table_width * 0.15)

        self.parameters_table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
        self.parameters_table.horizontalHeader().setStretchLastSection(True)
        self.parameters_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        self.parameters_table.paste_rows.connect(self.on_parameter_row_paste)
        # Add the parameters to the table.
        self.init_parameters_table()

        # ----------------------------------------------------------
        # Create the right side of the UI.
        self.right_widget = QtWidgets.QWidget()
        self.right_layout = QtWidgets.QVBoxLayout(self.right_widget)

        # Create the parameter properties group.
        self.properties_group = QtWidgets.QGroupBox('Parameter Properties')
        self.properties_group.setStyleSheet('QGroupBox::title { color: orange }')
        self.right_layout.addWidget(self.properties_group)
        self.property_grid_layout = QtWidgets.QGridLayout()
        self.properties_group.setLayout(self.property_grid_layout)

        # Create the name label inside the group.
        name_label = QtWidgets.QLabel('Name:')
        name_label.setMinimumWidth(self.min_label_text_width)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        name_label.setSizePolicy(size_policy)
        name_edit_widget = QtWidgets.QLineEdit('')
        name_edit_widget.setMinimumWidth(175)
        name_edit_widget.setReadOnly(True)
        name_edit_widget.setStyleSheet('color: rgb(120,120,120)')
        self.selected_parameter_name_widget = name_edit_widget
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        name_edit_widget.setSizePolicy(size_policy)
        self.property_grid_layout.addWidget(name_label, 0, 0, QtCore.Qt.AlignRight)
        self.property_grid_layout.addWidget(name_edit_widget, 0, 1)
        self.property_grid_layout.setColumnStretch(0, 0)
        self.property_grid_layout.setColumnStretch(1, 1)

        # Create the parameter property widgets.
        _, self.selected_parameter_default_widget = QtHelpers.add_float_field(layout=self.property_grid_layout,
                                                                              row_index=1,
                                                                              name='Default:', value=0.0, decimals=3,
                                                                              min_label_text_width=self.min_label_text_width)
        _, self.selected_parameter_minimum_widget = QtHelpers.add_float_field(layout=self.property_grid_layout,
                                                                              row_index=2,
                                                                              name='Minimum:', value=0.0, decimals=3,
                                                                              min_label_text_width=self.min_label_text_width)
        _, self.selected_parameter_maximum_widget = QtHelpers.add_float_field(layout=self.property_grid_layout,
                                                                              row_index=3,
                                                                              name='Maximum:', value=1.0, decimals=3,
                                                                              min_label_text_width=self.min_label_text_width)

        group_label = QtWidgets.QLabel('Group:')
        group_label.setMinimumWidth(self.min_label_text_width)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        group_label.setSizePolicy(size_policy)
        group_edit_widget = QtWidgets.QLineEdit('')
        group_edit_widget.setMinimumWidth(175)
        self.selected_group_name_widget = group_edit_widget
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        group_edit_widget.setSizePolicy(size_policy)
        self.property_grid_layout.addWidget(group_label, 4, 0, QtCore.Qt.AlignRight)
        self.property_grid_layout.addWidget(group_edit_widget, 4, 1)

        # Connect the widgets so we can capture changes.
        self.selected_parameter_default_widget.valueChanged.connect(self.on_selected_parameter_default_value_changed)
        self.selected_parameter_minimum_widget.valueChanged.connect(self.on_selected_parameter_min_value_changed)
        self.selected_parameter_maximum_widget.valueChanged.connect(self.on_selected_parameter_max_value_changed)
        self.selected_group_name_widget.textChanged.connect(self.on_selected_group_name_changed)

        self.right_layout.addWidget(self.properties_group)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.properties_group.setSizePolicy(size_policy)

        # ----------------------------------------------------------
        # Create the generator settings section.
        config = self.event_handler.generator_config
        self.generator_grid_layout = QtWidgets.QGridLayout()
        self.generator_group = QtWidgets.QGroupBox('Generator Settings')
        self.generator_group.setStyleSheet('QGroupBox::title { color: orange }')
        self.right_layout.addWidget(self.generator_group)
        self.generator_group.setLayout(self.generator_grid_layout)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.generator_group.setSizePolicy(size_policy)
        _, self.generator_settings_num_samples_widget = QtHelpers.add_int_field(layout=self.generator_grid_layout,
                                                                                row_index=0,
                                                                                name='Num Poses:',
                                                                                value=config.num_samples,
                                                                                min_value=1,
                                                                                min_label_text_width=self.min_label_text_width)
        _, self.generator_settings_start_frame_widget = QtHelpers.add_int_field(layout=self.generator_grid_layout,
                                                                                row_index=1,
                                                                                name='Start Frame:',
                                                                                value=config.start_frame,
                                                                                min_label_text_width=self.min_label_text_width)
        _, self.generator_settings_controller_probability_widget = QtHelpers.add_int_field(
            layout=self.generator_grid_layout,
            row_index=3,
            name='Active Parameters:',
            value=config.controller_probability * 100,
            min_value=0, max_value=100,
            min_label_text_width=self.min_label_text_width)
        _, self.generator_settings_set_max_probability_widget = QtHelpers.add_int_field(
            layout=self.generator_grid_layout,
            row_index=4,
            name='Force Max or Min:',
            value=config.set_max_min_probability * 100,
            min_value=0, max_value=100,
            min_label_text_width=self.min_label_text_width)

        self.generator_settings_controller_probability_widget.setSuffix(' %')
        self.generator_settings_set_max_probability_widget.setSuffix(' %')
        self.generator_grid_layout.setColumnStretch(0, 0)
        self.generator_grid_layout.setColumnStretch(1, 1)

        # Connect the settings widgets so we can capture the changes.
        self.generator_settings_num_samples_widget.valueChanged.connect(self.on_generator_settings_num_samples_changed)
        self.generator_settings_start_frame_widget.valueChanged.connect(self.on_generator_settings_start_frame_changed)
        self.generator_settings_controller_probability_widget.valueChanged.connect(
            self.on_generator_settings_controller_probability_changed)
        self.generator_settings_set_max_probability_widget.valueChanged.connect(
            self.on_generator_settings_set_max_probability_changed)

        # ----------------------------------------------------------
        # Create the collision settings section.
        self.collision_grid_layout = QtWidgets.QGridLayout()
        self.collision_group = QtWidgets.QGroupBox('Collision Settings')
        self.collision_group.setStyleSheet('QGroupBox::title { color: orange }')
        _, self.collision_mode_combo_box = QtHelpers.add_combo_box_field(
            layout=self.collision_grid_layout,
            row_index=config.collision_mode,
            name='Collision Detection:',
            combo_items=['None',
                         'Ray Mesh vs Collision Mesh',
                         'Bones vs Collision Mesh'],
            min_label_text_width=self.min_label_text_width)
        self.collision_mode_combo_box.currentIndexChanged.connect(self.on_collision_mode_changed)

        self.right_layout.addWidget(self.collision_group)
        self.collision_grid_layout.setColumnStretch(0, 0)
        self.collision_grid_layout.setColumnStretch(1, 1)
        self.collision_group.setLayout(self.collision_grid_layout)
        self.ray_mesh_widget = MeshFieldWidget(
            event_handler=self.event_handler,
            allow_multi_select=False,
            is_optional=False,
            place_holder_text='<ray mesh>')
        self.ray_mesh_widget.set_meshes([config.ray_mesh])
        self.ray_mesh_widget.meshes_changed.connect(self.on_generator_settings_ray_mesh_changed)
        self.collision_mesh_widget = MeshFieldWidget(
            event_handler=self.event_handler,
            allow_multi_select=False,
            is_optional=False,
            place_holder_text='<collision mesh>')
        self.collision_mesh_widget.set_meshes([config.collision_mesh])
        self.collision_mesh_widget.meshes_changed.connect(self.on_generator_settings_collision_mesh_changed)
        
        QtHelpers.add_widget_field(self.collision_grid_layout, row_index=1, name='Collision Mesh:', 
                                   widget=self.collision_mesh_widget,
                                   min_label_text_width=self.min_label_text_width,
                                   label_alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        
        QtHelpers.add_widget_field(self.collision_grid_layout, row_index=2, name='Ray Mesh:', 
                                   widget=self.ray_mesh_widget,
                                   min_label_text_width=self.min_label_text_width,
                                   label_alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        self.ray_mesh_widget.meshes_changed.connect(self.on_generator_settings_collision_retries_changed)
    
        _, self.collision_retry_attempt_widget = QtHelpers.add_int_field(
            layout=self.collision_grid_layout, row_index=3,
            name='Retry Attempts:',
            value=config.collision_retry_attempts,
            min_value=0,
            min_label_text_width=self.min_label_text_width)
        
        self.collision_retry_attempt_widget.valueChanged.connect(self.on_generator_settings_collision_retries_changed)

        _, self.allowed_collision_widget = QtHelpers.add_int_field(
            layout=self.collision_grid_layout, row_index=4,
            name='Allowed Collisions:',
            value=config.allowed_collisions,
            min_value=0,
            min_label_text_width=self.min_label_text_width)

        self.allowed_collision_widget.valueChanged.connect(self.on_generator_settings_allowed_collisions_changed)
        
    
        # ----------------------------------------------------------
        # Select the first parameter in the parameters table.
        self.parameters_table.itemSelectionChanged.connect(self.on_parameter_selection_changed)
        self.select_default_row()

        # ----------------------------------------------------------
        # Add a filler to fill the bottom of the right side.
        filler_widget = QtWidgets.QWidget()
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)
        filler_widget.setSizePolicy(size_policy)
        self.right_layout.addWidget(filler_widget)

        # ----------------------------------------------------------
        # Add the generate button.
        self.generate_button = QtWidgets.QPushButton('Generate')
        self.generate_button.clicked.connect(self.on_generate_button_pressed)
        self.right_layout.addWidget(self.generate_button)

        # ----------------------------------------------------------
        # Create the splitter.
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)
        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.right_widget)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        self.splitter.setSizes([950, 200])

        QtHelpers.center_window(self)

        self.update_ui_widgets()
        self.parameters_table.setColumnWidth(self.table_column__name, 450)

    def on_parameter_row_paste(self):
        copy_index = self.parameters_table.copied_index
        parameters = self.event_handler.generator_config.parameters
        if self.parameters_table.currentIndex().isValid():
            paste_index = self.parameters_table.currentIndex().row()
            if copy_index is not None and paste_index is not None and copy_index != paste_index: 
                parameters[paste_index].default_value = parameters[copy_index].default_value
                parameters[paste_index].min_value =  parameters[copy_index].min_value
                parameters[paste_index].max_value =  parameters[copy_index].max_value
                self.on_parameter_selection_changed()
                self.init_parameters_table()
            
    def on_collision_mode_changed(self):
        collision_mode_index = self.collision_mode_combo_box.currentIndex()
        self.event_handler.generator_config.collision_mode = collision_mode_index
        self.ray_mesh_widget.setEnabled(collision_mode_index == 1)
        self.collision_mesh_widget.setEnabled(collision_mode_index != 0)
        self.collision_retry_attempt_widget.setEnabled(collision_mode_index != 0)
        self.allowed_collision_widget.setEnabled(collision_mode_index == 1)

    def on_filter_text_changed(self, text):
        self.filter_text = text
        self.init_parameters_table()
        self.parameters_table.clearSelection()

    def disable_ui(self):
        self.main_widget.setEnabled(False)

    def enable_ui(self):
        self.main_widget.setEnabled(True)

    # Triggered when the parameter selection inside the parameters table changed.
    def on_parameter_selection_changed(self):
        self.selected_parameter_name_widget.blockSignals(True)
        self.selected_parameter_default_widget.blockSignals(True)
        self.selected_parameter_minimum_widget.blockSignals(True)
        self.selected_parameter_maximum_widget.blockSignals(True)
        self.selected_group_name_widget.blockSignals(True)

        selected_param_indices = self.get_selected_parameter_indices()
        if len(selected_param_indices) > 0:
            parameter = self.event_handler.generator_config.parameters[selected_param_indices[-1]]
            self.selected_parameter_name_widget.setText(parameter.display_name)
            self.selected_parameter_default_widget.setValue(parameter.default_value)
            self.selected_parameter_minimum_widget.setValue(parameter.min_value)
            self.selected_parameter_maximum_widget.setValue(parameter.max_value)
            self.selected_group_name_widget.setText(parameter.group_name)
        else:
            self.selected_parameter_name_widget.setText('')
            self.selected_parameter_default_widget.setValue(0.0)
            self.selected_parameter_minimum_widget.setValue(0.0)
            self.selected_parameter_maximum_widget.setValue(1.0)
            self.selected_group_name_widget.setText('')

        self.selected_parameter_name_widget.blockSignals(False)
        self.selected_parameter_default_widget.blockSignals(False)
        self.selected_parameter_minimum_widget.blockSignals(False)
        self.selected_parameter_maximum_widget.blockSignals(False)
        self.selected_group_name_widget.blockSignals(False)

    # Get a list of selected parameter indices.
    def get_selected_parameter_indices(self):
        resulting_indices = list()
        selected_items = self.parameters_table.selectedItems()
        col_count = self.parameters_table.columnCount()
        num_selected_rows = len(selected_items) // col_count
        assert (len(selected_items) % col_count) == 0, 'Expected entire row to be selected'
        for i in range(0, num_selected_rows):
            item = selected_items[i * col_count + self.table_column__name]
            param_index = item.data(QtCore.Qt.UserRole)
            resulting_indices.append(param_index)
        return resulting_indices

    # When the selected parameter's default value changed.
    def on_selected_parameter_default_value_changed(self):
        selected_param_indices = self.get_selected_parameter_indices()
        for index in selected_param_indices:
            new_value = self.selected_parameter_default_widget.value()
            self.event_handler.generator_config.parameters[index].default_value = new_value
            self.parameters_table.item(index, self.table_column__default).setText(str(new_value))
            self.update_parameter_colors(index)

    # When the selected parameter's minimum value changed.
    def on_selected_parameter_min_value_changed(self):
        selected_param_indices = self.get_selected_parameter_indices()
        for index in selected_param_indices:
            new_value = self.selected_parameter_minimum_widget.value()
            self.event_handler.generator_config.parameters[index].min_value = new_value
            self.parameters_table.item(index, self.table_column__minimum).setText(str(new_value))
            self.update_parameter_colors(index)

    # When the selected parameter's maximum value changed.
    def on_selected_parameter_max_value_changed(self):
        selected_param_indices = self.get_selected_parameter_indices()
        for index in selected_param_indices:
            new_value = self.selected_parameter_maximum_widget.value()
            self.event_handler.generator_config.parameters[index].max_value = new_value
            self.parameters_table.item(index, self.table_column__maximum).setText(str(new_value))
            self.update_parameter_colors(index)

    def on_selected_group_name_changed(self):
        selected_param_indices = self.get_selected_parameter_indices()
        for index in selected_param_indices:
            new_value = self.selected_group_name_widget.text()
            self.event_handler.generator_config.parameters[index].group_name = new_value
            self.parameters_table.item(index, self.table_column__group_name).setText(str(new_value))
            self.update_parameter_colors(index)

    # Generator settings number of samples changed.
    def on_generator_settings_num_samples_changed(self):
        self.event_handler.generator_config.num_samples = self.generator_settings_num_samples_widget.value()

    # Generator settings start frame changed.
    def on_generator_settings_start_frame_changed(self):
        self.event_handler.generator_config.start_frame = self.generator_settings_start_frame_widget.value()

    # Generator settings controller probability changed.
    def on_generator_settings_controller_probability_changed(self):
        self.event_handler.generator_config.controller_probability = self.generator_settings_controller_probability_widget.value() / 100.0

    # Generator settings controller probability changed.
    def on_generator_settings_set_max_probability_changed(self):
        self.event_handler.generator_config.set_max_min_probability = self.generator_settings_set_max_probability_widget.value() / 100.0
        
    def has_invalid_min_max_values(self):
        for parameter in self.event_handler.generator_config.parameters:
            if parameter.min_value > parameter.max_value:
                return True
        return False

    def on_generator_settings_ray_mesh_changed(self):
        if len(self.ray_mesh_widget.mesh_list) > 0:
            self.event_handler.generator_config.ray_mesh = self.ray_mesh_widget.mesh_list[0]

    def on_generator_settings_collision_mesh_changed(self):
        if len(self.ray_mesh_widget.mesh_list) > 0:
            self.event_handler.generator_config.collision_mesh = self.collision_mesh_widget.mesh_list[0]

    def on_generator_settings_collision_retries_changed(self):
        self.event_handler.generator_config.collision_retry_attempts = self.collision_retry_attempt_widget.value()

    def on_generator_settings_allowed_collisions_changed(self):
        self.event_handler.generator_config.allowed_collisions = self.allowed_collision_widget.value()
    
    # When we press the Generate button.
    def on_generate_button_pressed(self):
        config = self.event_handler.generator_config

        # Build a list of errors.
        pre_check_errors = list()

        if not config.parameters:
            error_text = 'There are <font color="orange">no parameters</font> yet. You add them by pressing the <font color=\'#00ff00\'><b>green</b></font> plus button.<br>'
            pre_check_errors.append(error_text)

        if not any(self.event_handler.get_parameter_exists(index) for index in range(0, len(config.parameters))):
            error_text = 'There are no existing parameters.<br>Please make sure you loaded the right config or {} scene.<br>'.format(
                self.event_handler.get_dcc_name())
            pre_check_errors.append(error_text)

        if self.has_invalid_min_max_values():
            error_text = 'There are <font color="orange">invalid</font> parameter min/max values, where min is greater than max.<br>'
            pre_check_errors.append(error_text)

        # Remove duplicates while preserving order.
        if pre_check_errors:
            seen = set()
            pre_check_errors = [x for x in pre_check_errors if not (x in seen or seen.add(x))]

        if pre_check_errors:
            error_message = \
                'Cannot continue because of the following errors:<br>' \
                '<ul style="margin-left:-30px">'
            for error in pre_check_errors:
                error_message += '<li>' + error + '</li>'
            error_message += '</ul>'

            QtWidgets.QMessageBox.critical(self, 'Cannot generate', error_message, QtWidgets.QMessageBox.Ok)
            return

        # Generate the animation.
        print('[MLDeformer] Generating {} frames with poses...'.format(config.num_samples))
        start_time = time.time()
        generate_success, generate_error = self.event_handler.generate()
        user_cancelled = self.event_handler.is_progress_bar_cancelled()
        self.event_handler.stop_progress_bar()  # Make sure we stop the progress bar.

        if user_cancelled:
            QtWidgets.QMessageBox.information(self, 'Operation cancelled', 'Generation cancelled by user.',
                                              QtWidgets.QMessageBox.Ok)
            return

        error_list = list()
        if len(generate_error) > 0:
            error_list.append(generate_error)

        if user_cancelled:
            QtWidgets.QMessageBox.information(self, 'Operation cancelled', 'Generation cancelled by user.',
                                              QtWidgets.QMessageBox.Ok)
            return

        # Report the elapsed time.
        end_time = time.time()
        elapsed_time = end_time - start_time
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_passed_string = str('{:0>2}:{:0>2}:{:0>2}'.format(int(hours), int(minutes), int(seconds)))
        print('[MLDeformer] Finished generating in {} (hh:mm:ss)'.format(time_passed_string))

        # Show errors if we had some.
        success = (len(error_list) == 0)
        if not success:
            error_message = \
                'There were some errors:<br>' \
                '<ul style="margin-left:-30px">'
            for error in error_list:
                error_message += '<li>' + error + '</li>'
            error_message += '</ul>'

            QtWidgets.QMessageBox.critical(self, 'Error Report', error_message, QtWidgets.QMessageBox.Ok)
        else:
            final_message = 'Successfully generated <b>{}</b> frames of training data using <b>{}</b> parameters!<br><br>'.format(
                config.num_samples, len(config.parameters))

            final_message += 'Generation time: <b>{}</b> (hh:mm:ss)'.format(time_passed_string)
            QtWidgets.QMessageBox.information(self, 'Finished Generating Training Data', final_message,
                                              QtWidgets.QMessageBox.Ok)

        self.enable_ui()
        self.close()

    # When we pressed the 'Add Parameters' button.
    def on_add_parameters_button_pressed(self):
        self.add_parameters_window = addParametersWindow(self, self.event_handler)
        self.add_parameters_window.add_button_pressed.connect(self.add_parameters)
        self.add_parameters_window.show()

    # Add the parameters from the add params window to this.
    def add_parameters(self):
        new_parameters = self.add_parameters_window.parameter_list
        for param in new_parameters:
            if not self.event_handler.generator_config.has_parameter(param.name):
                self.event_handler.generator_config.parameters.append(param)

        if len(self.event_handler.generator_config.parameters) > 0:
            self.event_handler.generator_config.parameters.sort(key=lambda x: x.display_name.lower())

        self.init_parameters_table()
        self.parameters_table.clearSelection()
        if self.parameters_table.rowCount() > 0:
            self.select_default_row()
            self.on_parameter_selection_changed()

    # Show the parameter defaults configuration window.
    def on_parameter_defaults_configure(self):
        self.param_defaults_window = ParamMinMaxSetupWindow(self, self.event_handler)
        self.param_defaults_window.exec_()

    # Remove a given list of parameters, where the remove list is a list of indices.
    def remove_parameters_by_index_list(self, remove_list):
        for index in sorted(remove_list, reverse=True):
            self.parameters_table.removeRow(index)
            del self.event_handler.generator_config.parameters[index]

        # Init the table again, which stores the user data parameter indices correctly again.
        self.init_parameters_table()

        if len(remove_list) > 0:
            selection_index = sorted(remove_list)[0]
            if selection_index < self.parameters_table.rowCount():
                self.parameters_table.selectRow(selection_index)
            else:
                self.parameters_table.selectRow(self.parameters_table.rowCount() - 1)

    # Remove all non-existing parameters.
    def remove_non_existing_parameters(self):
        remove_list = list()
        for i in range(0, len(self.event_handler.generator_config.parameters)):
            if not self.get_parameter_exists(i):
                remove_list.append(i)
        self.remove_parameters_by_index_list(remove_list)

    # Remove all selected parameters.
    def remove_selected_parameters(self):
        remove_list = self.get_selected_parameter_indices()
        self.remove_parameters_by_index_list(remove_list)

    # Remove all parameters, clearing the table.
    def remove_all_parameters(self):
        remove_list = list(range(0, len(self.event_handler.generator_config.parameters)))
        self.remove_parameters_by_index_list(remove_list)
        self.init_parameters_table()

    # Some key got pressed.
    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Delete:
            self.remove_selected_parameters()

    # Update this UI.
    def update(self):
        self.update_ui_widgets()

    # Update the values in all widgets, with the values in the current configuration.
    # This is called after loading a config for example, to refresh all UI widget values.
    def update_ui_widgets(self):
        config = self.event_handler.generator_config

        self.generator_settings_num_samples_widget.setValue(config.num_samples)
        self.generator_settings_start_frame_widget.setValue(config.start_frame)
        self.generator_settings_controller_probability_widget.setValue(config.controller_probability * 100)
        self.auto_load_last_config_action.setChecked(self.event_handler.global_settings.auto_load_last_config)
        self.ray_mesh_widget.set_meshes([config.ray_mesh])
        self.collision_mesh_widget.set_meshes([config.collision_mesh])
        self.collision_mode_combo_box.setCurrentIndex(config.collision_mode)
        self.collision_retry_attempt_widget.setValue(config.collision_retry_attempts)
        self.allowed_collision_widget.setValue(config.allowed_collisions)
        self.on_generator_settings_collision_mesh_changed()
        self.on_generator_settings_ray_mesh_changed()
        self.on_collision_mode_changed()
        self.init_parameters_table()

    # Resize the row heights to fit the contents nicely when we resize the window.
    def resizeEvent(self, event):
        QtWidgets.QMainWindow.resizeEvent(self, event)
        self.parameters_table.resizeRowsToContents()
        self.parameters_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)

    # Check if we have non existing parameters. This happens when deleting objects, or loading a config for the wrong scene.
    def has_non_existing_parameters(self):
        for param_index in range(0, len(self.event_handler.generator_config.parameters)):
            if not self.get_parameter_exists(param_index):
                return True
        return False

    # The context menu that pops up when you right click the table.
    def on_table_context_menu(self, point):
        if self.parameters_table.rowCount() == 0:
            return

        menu = QtWidgets.QMenu(self)
        selected_param_indices = self.get_selected_parameter_indices()
        remove_selected_action = None
        if len(selected_param_indices) > 0:
            remove_selected_action = menu.addAction('Remove selected parameters')

        remove_non_existing_parameters_action = None
        if self.has_non_existing_parameters():
            remove_non_existing_parameters_action = menu.addAction('Remove non-existing parameters')

        if selected_param_indices:
            menu.addSeparator()

        clear_action = menu.addAction('Clear')

        # Spawn the context menu and handle the action that was picked in the context menu.
        action = menu.exec_(self.mapToGlobal(point))
        if action:
            if remove_selected_action and action == remove_selected_action:
                self.remove_selected_parameters()
            elif remove_non_existing_parameters_action and action == remove_non_existing_parameters_action:
                self.remove_non_existing_parameters()
            elif action == clear_action:
                self.remove_all_parameters()

    # Check if a given parameter exists or not.
    def get_parameter_exists(self, parameter_index):
        return self.event_handler.get_parameter_exists(parameter_index)

    # Check if we have a valid minimum and maximum value.
    def get_has_valid_min_max(self, parameter_index):
        parameter = self.event_handler.generator_config.parameters[parameter_index]
        return parameter.min_value <= parameter.max_value

    # Check if the default value is in between the minimum and maximum value
    def get_has_valid_default_value(self, parameter_index):
        parameter = self.event_handler.generator_config.parameters[parameter_index]
        return (parameter.default_value >= parameter.min_value) and (parameter.default_value <= parameter.max_value)

    # Update the table colors for a given parameter.
    def update_parameter_colors(self, param_index):
        # Get the table widget items.
        name_item = self.parameters_table.item(param_index, self.table_column__name)
        default_value_item = self.parameters_table.item(param_index, self.table_column__default)
        min_value_item = self.parameters_table.item(param_index, self.table_column__minimum)
        max_value_item = self.parameters_table.item(param_index, self.table_column__maximum)
        object_type_item = self.parameters_table.item(param_index, self.table_column__object_type)
        group_name_item = self.parameters_table.item(param_index, self.table_column__group_name)

        # Init at default colors.
        name_item.setForeground(self.table_default_foreground_brush)
        min_value_item.setForeground(self.table_default_foreground_brush)
        max_value_item.setForeground(self.table_default_foreground_brush)
        default_value_item.setForeground(self.table_default_foreground_brush)
        object_type_item.setForeground(self.table_default_foreground_brush)
        group_name_item.setForeground(self.table_default_foreground_brush)

        # Modify colors.
        if not self.get_parameter_exists(param_index):
            name_item.setForeground(self.dark_gray_brush)
            min_value_item.setForeground(self.dark_gray_brush)
            max_value_item.setForeground(self.dark_gray_brush)
            default_value_item.setForeground(self.dark_gray_brush)
            object_type_item.setForeground(self.dark_gray_brush)
        else:
            if not self.get_has_valid_min_max(param_index):
                min_value_item.setForeground(self.red_brush)
                max_value_item.setForeground(self.red_brush)

            if not self.get_has_valid_default_value(param_index):
                default_value_item.setForeground(self.red_brush)

    # Update the contents of the parameters table by clearing and refilling it.
    def init_parameters_table(self):
        if len(self.event_handler.generator_config.parameters) == 0:
            self.parameters_table.hide()
            self.parameters_label.setText('Parameters ({})'.format(len(self.event_handler.generator_config.parameters)))
            self.main_message.show()
            return

        self.main_message.hide()
        self.parameters_table.show()
        self.parameters_table.setColumnWidth(self.table_column__name, 400)
        self.parameters_table.setEnabled(True)
        self.parameters_table.setShowGrid(True)
        self.parameters_table.horizontalHeader().show()
        self.parameters_table.setRowCount(len(self.event_handler.generator_config.parameters))

        for row, parameter in enumerate(self.event_handler.generator_config.parameters):
            # Check the filter.
            hidden = False
            if len(self.filter_text) > 0:
                if not search(self.filter_text, parameter.display_name):
                    hidden = True

            name_item = QtWidgets.QTableWidgetItem(parameter.display_name)
            name_item.setData(QtCore.Qt.UserRole, row)
            self.parameters_table.setItem(row, self.table_column__name, name_item)

            default_value_item = QtWidgets.QTableWidgetItem(str(parameter.default_value))
            self.parameters_table.setItem(row, self.table_column__default, default_value_item)

            min_value_item = QtWidgets.QTableWidgetItem(str(parameter.min_value))
            self.parameters_table.setItem(row, self.table_column__minimum, min_value_item)

            max_value_item = QtWidgets.QTableWidgetItem(str(parameter.max_value))
            self.parameters_table.setItem(row, self.table_column__maximum, max_value_item)

            object_type_item = QtWidgets.QTableWidgetItem(str(parameter.object_type))
            self.parameters_table.setItem(row, self.table_column__object_type, object_type_item)

            group_name_item = QtWidgets.QTableWidgetItem(str(parameter.group_name))
            self.parameters_table.setItem(row, self.table_column__group_name, group_name_item)

            self.update_parameter_colors(row)

            if hidden:
                self.parameters_table.hideRow(row)
            else:
                self.parameters_table.showRow(row)

        self.parameters_table.resizeRowsToContents()
        self.parameters_label.setText('Parameters ({})'.format(len(self.event_handler.generator_config.parameters)))
        if len(self.parameters_table.selectedItems()) == 0 and self.parameters_table.rowCount() > 0:
            self.parameters_table.selectRow(0)
