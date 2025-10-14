# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

import os
from mldeformer.ui.Qt import QtCore, QtGui, QtWidgets

class FolderPickerFieldWidget(QtWidgets.QWidget):
    folder_picked = QtCore.Signal(str)

    def __init__(self, event_handler, initial_folder, caption):
        super(FolderPickerFieldWidget, self).__init__(None)

        self.initial_folder = initial_folder
        self.caption = caption
        self.error_text = ''
        self.event_handler = event_handler

        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(2)
        self.setLayout(self.main_layout)

        self.folder_line_edit = QtWidgets.QLineEdit(initial_folder)
        self.folder_line_edit.setToolTip(initial_folder)
        self.folder_line_edit.setReadOnly(True)
        self.main_layout.addWidget(self.folder_line_edit)

        self.pick_folder_button = QtWidgets.QPushButton(QtGui.QIcon(self.event_handler.open_icon_path), '')
        self.pick_folder_button.setFixedSize(20, 20)
        self.pick_folder_button.clicked.connect(self.on_pick_folder_button_pressed)
        self.pick_folder_button.setToolTip('Pick a folder.')
        self.main_layout.addWidget(self.pick_folder_button)

        self.set_folder(initial_folder)

    def set_folder(self, folder):
        self.folder_line_edit.setText(folder)
        self.error_text = ''
        tool_tip_text = "<style>p { margin: 0 0 0 0 }</style><p style='white-space:pre'>"
        if os.path.exists(folder):
            self.folder_line_edit.setStyleSheet('')
            self.folder_line_edit.setToolTip(folder)
        else:
            self.error_text = 'Folder <b>{}</b> <font color="orange">doesn''t exist!</font>'.format(folder)
            tool_tip_text += '<font color="red">Folder <b>{}</b> does not exist!</font><br>'.format(folder)
            self.folder_line_edit.setStyleSheet(
                'QLineEdit { border-width: 0px 3px 0px 0px; border-style: solid; border-color: rgb(255,80,0) }')
            self.folder_line_edit.setToolTip(tool_tip_text)

        self.folder_picked.emit(folder)

    def on_pick_folder_button_pressed(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption=self.caption,
            dir=self.initial_folder)

        if len(folder) > 0:
            self.set_folder(folder)

    def get_folder(self):
        return self.folder_line_edit.text()
