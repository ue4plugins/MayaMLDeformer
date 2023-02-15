# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

import os
import time
from re import search

import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from mldeformer.ui.qtgui.helpers import QtHelpers
from mldeformer.ui.qtgui.file_picker_field_widget import FilePickerFieldWidget
from mldeformer.ui.qtgui.mesh_mapping_widget import MeshMappingWidget
from mldeformer.ui.qtgui.top_level_window import TopLevelWindow

class DeformerExportWindow(TopLevelWindow):
    min_label_text_width = 120
    main_button_size = 22
    export_files_pressed = QtCore.Signal()
    cancel_pressed = QtCore.Signal()

    def __init__(self, event_handler):
        super(DeformerExportWindow, self).__init__(event_handler)
        self.event_handler = event_handler

        self.setWindowIcon(QtGui.QIcon(self.event_handler.unreal_icon_path))

        self.red_brush = QtGui.QBrush(QtGui.QColor(255, 80, 0))
        self.dark_gray_brush = QtGui.QBrush(QtGui.QColor(95, 95, 95))
        self.table_default_foreground_brush = QtGui.QBrush(QtGui.QColor(200, 200, 200))

        self.init_ui()

    # Initialize the main UI.
    def init_ui(self):
        print('[MLDeformer] Creating Export UI')

        # Create the main window.
        self.setObjectName('MLDeformerExporterWindow')
        self.setWindowTitle('MLDeformer (Unreal Engine) - Export')
        self.main_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.main_widget)
        
        self.main_layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.main_layout.setSpacing(2)
        config = self.event_handler.generator_config
        self.create_main_menu()

        # Create the mesh settings section.
        self.mesh_grid_layout = QtWidgets.QGridLayout()
        self.mesh_group = QtWidgets.QGroupBox('Mesh Settings')
        self.mesh_group.setStyleSheet('QGroupBox::title { color: orange }')
        self.main_layout.addWidget(self.mesh_group)
        self.mesh_grid_layout.setColumnStretch(0, 0)
        self.mesh_grid_layout.setColumnStretch(1, 1)
        self.mesh_group.setLayout(self.mesh_grid_layout)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.mesh_group.setSizePolicy(size_policy)

        self.mesh_widget = MeshMappingWidget(self.event_handler)
        self.mesh_widget.contents_changed.connect(self.on_mesh_mappings_changed)
        QtHelpers.add_widget_field(self.mesh_grid_layout, row_index=0, name='Meshes:', widget=self.mesh_widget,
                                   min_label_text_width=self.min_label_text_width)

        # ----------------------------------------------------------
        # Create the output section.
        self.output_grid_layout = QtWidgets.QGridLayout()
        self.output_group = QtWidgets.QGroupBox('Output Settings')
        self.output_group.setStyleSheet('QGroupBox::title { color: orange }')
        self.main_layout.addWidget(self.output_group)
        self.output_grid_layout.setColumnStretch(0, 0)
        self.output_grid_layout.setColumnStretch(1, 1)
        self.output_group.setLayout(self.output_grid_layout)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.output_group.setSizePolicy(size_policy)

        start_frame = cmds.playbackOptions(q=True, ast=True)
        end_frame = cmds.playbackOptions(q=True, aet=True)
        
        _, self.start_frame_widget = QtHelpers.add_int_field(layout=self.output_grid_layout,
                                                             row_index=0, name='Start Frame:', 
                                                             value=start_frame,
                                                             min_label_text_width=self.min_label_text_width)
        
        _, self.end_frame_widget = QtHelpers.add_int_field(layout=self.output_grid_layout,
                                                             row_index=1, name='End Frame:', 
                                                             value=end_frame,
                                                             min_label_text_width=self.min_label_text_width)
        
        self.output_fbx_file_widget = FilePickerFieldWidget(
            event_handler=self.event_handler,
            has_check_box=True,
            is_checked=config.save_target_alembic,
            filename=config.output_fbx_file,
            file_type_description='Fbx Files (*.Fbx)',
            default_dir=self.event_handler.output_path,
            caption='save Fbx as...')
        QtHelpers.add_widget_field(self.output_grid_layout, row_index=2, name='Base Fbx File:',
                                   widget=self.output_fbx_file_widget, min_label_text_width=self.min_label_text_width)

        self.output_abc_file_widget = FilePickerFieldWidget(
            event_handler=self.event_handler,
            has_check_box=True,
            is_checked=config.save_target_alembic,
            filename=config.output_abc_file,
            file_type_description='Alembic (*.Abc)',
            default_dir=self.event_handler.output_path,
            caption='Save Alembic file as...')
        QtHelpers.add_widget_field(self.output_grid_layout, row_index=3, name='Target Alembic File:',
                                   widget=self.output_abc_file_widget, min_label_text_width=self.min_label_text_width)


        self.output_fbx_file_widget.file_picked.connect(self.on_output_fbx_file_picked)
        self.output_abc_file_widget.file_picked.connect(self.on_output_abc_file_picked)
        self.output_abc_file_widget.check_box_changed.connect(self.on_output_abc_file_check_box_changed)

        # ----------------------------------------------------------
        # Add the export and cancel button 
        self.export_cancel_layout = QtWidgets.QHBoxLayout()
        self.export_cancel_layout.setSpacing(2)
        self.export_button = QtWidgets.QPushButton('Export')
        self.export_button.clicked.connect(self.on_export_button_pressed)
        self.export_cancel_layout.addWidget(self.export_button)
        self.cancel_button = QtWidgets.QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.on_cancel_button_pressed)
        self.export_cancel_layout.addWidget(self.cancel_button)
        self.main_layout.addLayout(self.export_cancel_layout)

        QtHelpers.center_window(self)
        self.resize(400, 400)
        self.update_ui_widgets()
    
    def update_ui_widgets(self):
        config = self.event_handler.generator_config
        self.output_fbx_file_widget.set_filename(config.output_fbx_file)
        self.output_fbx_file_widget.enabled_check_box.setChecked(config.save_target_alembic)
        self.output_abc_file_widget.set_filename(config.output_abc_file)
        self.output_abc_file_widget.enabled_check_box.setChecked(config.save_target_alembic)
        self.mesh_widget.update()
        self.on_mesh_mappings_changed()
        
    # When we press the Export button.
    def on_export_button_pressed(self):
        config = self.event_handler.generator_config

        # Build a list of errors.
        pre_check_errors = list()
            
        mesh_mapping_index = self.event_handler.get_first_enabled_mesh_mapping_index()
        if mesh_mapping_index == -1:  # We have no enabled meshes to export.
            error_text = 'There are no enabled mesh mappings, please add some meshes or enable at least one.'
            pre_check_errors.append(error_text)

        self.mesh_widget.update_error_text()
        if self.mesh_widget.error_text:
            pre_check_errors.append(self.mesh_widget.error_text)

        if self.output_fbx_file_widget.error_text:
            pre_check_errors.append(self.output_fbx_file_widget.error_text)

        if self.output_abc_file_widget.is_checked() and self.output_abc_file_widget.error_text:
            pre_check_errors.append(self.output_abc_file_widget.error_text)

        error_list = list()
        start_time = time.time()
        cmds.refresh(suspend=True)

        try:
            # save the Fbx.
            if self.output_fbx_file_widget.is_checked():
                print('[MLDeformer] Saving Fbx to file {}'.format(config.output_fbx_file))
                self.event_handler.start_progress_bar('Saving Fbx...')
                saved_fbx, fbx_error_message = self.event_handler.save_fbx()
                if not saved_fbx:
                    error_message = 'Failed to save Fbx file:<br><b>' + config.output_fbx_file + '</b><br><font color="yellow">' + fbx_error_message + '</font>'
                    error_list.append(error_message)
                    print('[MLDeformer] Failed to save Fbx file')
                user_cancelled = self.event_handler.is_progress_bar_cancelled()
                self.event_handler.stop_progress_bar()

            if user_cancelled:
                QtWidgets.QMessageBox.information(self, 'Operation cancelled', 'Generation cancelled by user.',
                                                  QtWidgets.QMessageBox.Ok)
                return

            # save the Alembic if we enabled exporting it, and if there is actually a target mesh.
            if self.output_abc_file_widget.is_checked() and (
                self.event_handler.get_first_enabled_mesh_mapping_index_with_target_mesh() != -1):
                print('[MLDeformer] Saving Alembic to file {}'.format(config.output_abc_file))
                self.event_handler.start_progress_bar('Saving Alembic...')
                saved_alembic, abc_error_message = self.event_handler.save_alembic()
                if not saved_alembic:
                    error_message = 'Failed to save Alembic file:<br><b>' + config.output_abc_file + '</b><br><font color="yellow">' + abc_error_message + '</font>'
                    error_list.append(error_message)
                    print('[MLDeformer] Failed to save Alembic file')
                user_cancelled = self.event_handler.is_progress_bar_cancelled()
                self.event_handler.stop_progress_bar()
        except RuntimeError:
            error_message = 'Unexpected runtime error when saving fbx or alembic file'
            error_list.append(error_message)
            print('[MLDeformer] Unexpected runtime error')
        finally:
            cmds.refresh(suspend=False)

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
        print('[MLDeformer] Finished exporting in {} (hh:mm:ss)'.format(time_passed_string))

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
            # Extract path and filename from Fbx file.
            fbx_folder = os.path.dirname(os.path.abspath(config.output_fbx_file))
            fbx_folder = fbx_folder.replace('\\', '/')  # Needed to make links opening the folder.
            fbx_file = os.path.basename(os.path.abspath(config.output_fbx_file))

            # Extract path and filename from Alembic file.
            abc_folder = os.path.dirname(os.path.abspath(config.output_abc_file))
            abc_folder = abc_folder.replace('\\', '/')  # Needed to make links opening the folder.
            abc_file = os.path.basename(os.path.abspath(config.output_abc_file))

            final_message = ""
            
            if self.output_fbx_file_widget.is_checked():
                final_message += 'Output Fbx: <a href=\'{}\'><span style=\'color:white;\'>{}</span></a><b>/{}</b><br><br>'.format(
                    fbx_folder, fbx_folder, fbx_file)

            if self.output_abc_file_widget.is_checked():
                final_message += 'Output Abc: <a href=\'{}\'><span style=\'color:white;\'>{}</span></a><b>/{}</b><br><br>'.format(
                    abc_folder, abc_folder, abc_file)

            final_message += 'Generation time: <b>{}</b> (hh:mm:ss)'.format(time_passed_string)
            QtWidgets.QMessageBox.information(self, 'Finished Generating Training Data', final_message,
                                              QtWidgets.QMessageBox.Ok)

        self.close()
        self.export_files_pressed.emit()
        # When we press the Export button.

    def on_cancel_button_pressed(self):
        self.close()
        self.cancel_pressed.emit()
        
    def on_mesh_mappings_changed(self):
        mapping_index_with_target = self.event_handler.get_first_enabled_mesh_mapping_index_with_target_mesh()
            
    def on_output_fbx_file_picked(self, file_path):
        self.event_handler.generator_config.output_fbx_file = file_path
        
    def on_output_abc_file_picked(self, file_path):
        self.event_handler.generator_config.output_abc_file = file_path

    def on_output_abc_file_check_box_changed(self, is_checked):
        self.event_handler.generator_config.save_target_alembic = is_checked

    def on_output_fbx_file_check_box_changed(self, is_checked):
        self.event_handler.generator_config.save_target_fbx = is_checked

    def select_listed_meshes(mesh_list):
        shapes_list = cmds.ls(selection=False, long=True, objectsOnly=True, geometry=True, type='mesh')
        meshes_to_remove = set()
        if shapes_list:
            all_meshes = cmds.listRelatives(shapes_list, parent=True)
            meshes_to_remove = set(all_meshes) - set(mesh_list)  # Remove duplicates and sort by name

        all_objects = cmds.ls()
        objects_to_select = list(set(all_objects) - meshes_to_remove)
        cmds.select(objects_to_select)
