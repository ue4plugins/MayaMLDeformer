# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

import os

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

from mldeformer.ui.event_handler import EventHandler


class FilePickerFieldWidget(QtWidgets.QWidget):
    file_picked = QtCore.Signal(str)
    check_box_changed = QtCore.Signal(bool)

    def __init__(self, event_handler, has_check_box, is_checked, filename, file_type_description, default_dir, caption):
        super(FilePickerFieldWidget, self).__init__(None)

        self.event_handler = event_handler
        self.default_dir = default_dir
        self.file_type_description = file_type_description
        self.caption = caption
        self.error_text = ''

        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(2)
        self.setLayout(self.main_layout)

        if has_check_box:
            self.enabled_check_box = QtWidgets.QCheckBox()
            self.enabled_check_box.stateChanged.connect(self.on_check_box_changed)
            self.enabled_check_box.setToolTip('Enable saving this file? Uncheck if you want to skip saving this file.')
            self.main_layout.addWidget(self.enabled_check_box)
        else:
            self.enabled_check_box = None

        self.file_name_line_edit = QtWidgets.QLineEdit(filename)
        self.file_name_line_edit.setToolTip(filename)
        self.file_name_line_edit.setReadOnly(True)
        self.main_layout.addWidget(self.file_name_line_edit)

        self.pick_file_button = QtWidgets.QPushButton(QtGui.QIcon(self.event_handler.open_icon_path), '')
        self.pick_file_button.setFixedSize(20, 20)
        self.pick_file_button.clicked.connect(self.on_pick_file_button_pressed)
        self.pick_file_button.setToolTip('Specify an output file.')
        self.main_layout.addWidget(self.pick_file_button)

        self.set_filename(filename)
        self.set_checked(is_checked)
        self.on_check_box_changed()

    def is_checked(self):
        if self.enabled_check_box:
            return self.enabled_check_box.isChecked()
        return True

    def set_checked(self, is_checked):
        if self.enabled_check_box:
            self.enabled_check_box.setChecked(is_checked)

    def on_check_box_changed(self):
        enabled = self.enabled_check_box.isChecked() if self.enabled_check_box else True
        self.file_name_line_edit.setEnabled(enabled)
        self.pick_file_button.setEnabled(enabled)
        self.check_box_changed.emit(enabled)

    def set_filename(self, filename):
        file_without_path = os.path.basename(filename)
        self.file_name_line_edit.setText(file_without_path)

        self.error_text = ''
        tool_tip_text = "<style>p { margin: 0 0 0 0 }</style><p style='white-space:pre'>"
        folder = os.path.dirname(filename)
        if os.path.exists(folder):
            self.file_name_line_edit.setStyleSheet('')
        else:
            self.error_text = 'Output folder <b>{}</b> <font color="orange">doesn''t exist!</font>'.format(folder)
            tool_tip_text += '<font color="red">Folder <b>{}</b> does not exist!</font><br>'.format(folder)
            self.file_name_line_edit.setStyleSheet(
                'QLineEdit { border-width: 0px 3px 0px 0px; border-style: solid; border-color: rgb(255,80,0) }')

        tool_tip_text += filename

        self.file_name_line_edit.setToolTip(tool_tip_text)
        self.file_picked.emit(filename)

    def on_pick_file_button_pressed(self):
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption=self.caption,
            dir=self.default_dir,
            filter=self.file_type_description)

        if len(file_path) > 0:
            self.set_filename(file_path)
