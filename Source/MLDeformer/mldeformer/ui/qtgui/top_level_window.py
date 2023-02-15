# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved
import os
from PySide2 import QtGui
from PySide2 import QtWidgets
from mldeformer.ui.recent_file_list import RecentFileList
from mldeformer.ui.config import Config
from mldeformer.ui.qtgui.param_minmax_setup_window import ParamMinMaxSetupWindow


class TopLevelWindow(QtWidgets.QMainWindow):

    def __init__(self, event_handler):
        super(TopLevelWindow, self).__init__(event_handler.get_parent_window())
        self.event_handler = event_handler
        self.filter_text = ''
        if self.event_handler.global_settings.auto_load_last_config:
            self.load_config_file(self.event_handler.last_config_file, init_ui=False, update_recent_file_list=False)

        self.recent_config_list_file = os.path.join(self.event_handler.rig_deformer_path, 'Recent.configList')
        self.recent_config_list = RecentFileList()
        self.recent_config_list.load(self.recent_config_list_file)

    # Create the main menu bar.
    def create_main_menu(self):
        self.main_menu = self.menuBar()
        self.file_menu = self.main_menu.addMenu('File')

        self.configure_menu = self.main_menu.addMenu('Configure')
        self.attribute_min_max_values_config_action = QtWidgets.QAction('Attribute Min/Max Setup', self)
        self.configure_menu.addAction(self.attribute_min_max_values_config_action)
        self.attribute_min_max_values_config_action.triggered.connect(self.on_parameter_defaults_configure)

        self.reset_config_action = QtWidgets.QAction('Reset Current Config', self)
        self.configure_menu.addAction(self.reset_config_action)
        self.reset_config_action.setShortcut('Ctrl+R')
        self.reset_config_action.triggered.connect(self.on_reset_config)

        self.configure_menu.addSeparator()

        self.auto_load_last_config_action = QtWidgets.QAction('Auto Load Last Config', self)
        self.auto_load_last_config_action.setCheckable(True)
        self.auto_load_last_config_action.setChecked(self.event_handler.global_settings.auto_load_last_config)
        self.configure_menu.addAction(self.auto_load_last_config_action)
        self.auto_load_last_config_action.triggered.connect(self.on_toggle_auto_load_last_config)

        # Open a config file. 
        open_action = QtWidgets.QAction(QtGui.QIcon(self.event_handler.open_icon_path), 'Load config', self)
        open_action.setShortcut('Ctrl+O')
        self.file_menu.addAction(open_action)
        open_action.triggered.connect(self.on_load_config)

        # save a config file.
        save_action = QtWidgets.QAction(QtGui.QIcon(self.event_handler.save_icon_path), 'Save config', self)
        save_action.setShortcut('Ctrl+S')
        self.file_menu.addAction(save_action)
        save_action.triggered.connect(self.on_save_config)

        self.file_menu.addSeparator()

        self.recent_configs_menu = self.file_menu.addMenu('Recent Configs')
        self.fill_recent_configs_menu()

    def fill_recent_configs_menu(self):
        self.recent_configs_menu.clear()
        for item in reversed(self.recent_config_list.file_list):
            action = self.recent_configs_menu.addAction(item)
            action.triggered.connect(self.on_recent_config)

    def on_recent_config(self):
        action = self.sender()
        self.load_config_file(action.text(), init_ui=True, update_recent_file_list=True)

    # When the 'Auto Load Last Config' menu option toggles on or off.
    def on_toggle_auto_load_last_config(self):
        self.event_handler.global_settings.auto_load_last_config = self.auto_load_last_config_action.isChecked()

    # Reset the config to defaults.
    def on_reset_config(self):
        self.event_handler.generator_config = Config(self.event_handler.rig_deformer_path)
        self.update_ui_widgets()

    # Load some pre-saved configuration file.
    def on_load_config(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption='Load configuration from...',
            dir=self.event_handler.rig_deformer_path,
            filter='Configuration Files (*.json)')

        if len(file_path) > 0:
            self.load_config_file(file_path)

    # Load a config from a file.
    def load_config_file(self, file_path, init_ui=True, update_recent_file_list=True):
        self.event_handler.generator_config.load_from_file(file_path)
        if update_recent_file_list:
            self.recent_config_list.add(file_path)
            self.recent_config_list.save(self.recent_config_list_file)
            self.fill_recent_configs_menu()

        if init_ui:
            self.update_ui_widgets()

    # save the current configuration to a file.
    def on_save_config(self):
        # Show the save as dialog.
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption='Save configuration as...',
            dir=self.event_handler.rig_deformer_path,
            filter='Configuration Files (*.json)')

        # If we selected a valid filename.
        if len(file_path) > 0:
            self.event_handler.generator_config.save_to_file(file_path)
            self.recent_config_list.add(file_path)
            self.recent_config_list.save(self.recent_config_list_file)
            
    # Show the parameter defaults configuration window.
    def on_parameter_defaults_configure(self):
        self.param_defaults_window = ParamMinMaxSetupWindow(self, self.event_handler)
        self.param_defaults_window.exec_()
