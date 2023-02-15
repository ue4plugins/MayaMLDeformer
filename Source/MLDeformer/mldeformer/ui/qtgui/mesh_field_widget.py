# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui

from mldeformer.ui.event_handler import EventHandler
from mldeformer.ui.qtgui.mesh_list_picker import MeshListPicker


class MeshFieldWidget(QtWidgets.QWidget):
    meshes_changed = QtCore.Signal(list)
    widget_height = 22

    def __init__(self, event_handler, allow_multi_select=True, is_optional=False, place_holder_text=''):
        super(MeshFieldWidget, self).__init__(None)

        self.event_handler = event_handler
        self.allow_multi_select = allow_multi_select
        self.is_optional = is_optional
        self.mesh_list = list()
        self.error_text = ''

        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(2)
        self.setLayout(self.main_layout)

        self.mesh_list_widget = QtWidgets.QLineEdit('')
        self.mesh_list_widget.setReadOnly(True)
        self.mesh_list_widget.setPlaceholderText(place_holder_text)
        self.mesh_list_widget.setFixedHeight(self.widget_height)
        self.main_layout.addWidget(self.mesh_list_widget)

        self.mesh_select_button = QtWidgets.QPushButton('<<')
        self.mesh_select_button.setFixedHeight(self.widget_height)
        self.mesh_select_button.clicked.connect(self.on_add_selected_mesh_button_pressed)
        self.main_layout.addWidget(self.mesh_select_button)

        self.mesh_select_button = QtWidgets.QPushButton(QtGui.QIcon(self.event_handler.add_icon_path), '')
        self.mesh_select_button.setFixedHeight(self.widget_height)
        self.mesh_select_button.clicked.connect(self.on_select_mesh_button_pressed)
        self.main_layout.addWidget(self.mesh_select_button)

    def set_meshes(self, mesh_list):
        self.error_text = ''
        text = ''
        missing_meshes = list()
        for item in mesh_list:
            if not item:
                continue
            if item not in self.event_handler.get_mesh_list():
                missing_meshes.append(item)
            text += item + ', '
        text = text.rstrip(', ')
        self.mesh_list_widget.setText(text)
        self.mesh_list_widget.setToolTip('')

        tool_tip_text = "<style>p { margin: 0 0 0 0 }</style><p style='white-space:pre'>"
        has_tool_tip = False
        if not self.is_optional:
            if not text:
                has_tool_tip = True
                self.error_text = 'A mesh needs to be selected.'
                tool_tip_text = 'Please select a mesh, as it is required!'
                self.mesh_list_widget.setStyleSheet(
                    'QLineEdit { border-width: 0px 3px 0px 0px; border-style: solid; border-color: yellow }')
            else:
                self.mesh_list_widget.setStyleSheet('')

        for mesh_name in mesh_list:
            if not mesh_name:
                continue
            has_tool_tip = True
            if mesh_name not in missing_meshes:
                tool_tip_text += mesh_name + '<br>'
            else:
                self.error_text += 'Mesh object <b>' + mesh_name + '</b> is <font color="orange">missing</font> in the scene.<br>'
                tool_tip_text += mesh_name + '<font color="red"> (missing)</font><br>'

            tool_tip_text = tool_tip_text.rstrip('<br>')

        if missing_meshes:
            self.mesh_list_widget.setStyleSheet(
                'QLineEdit { border-width: 0px 3px 0px 0px; border-style: solid; border-color: rgb(255,80,0) }')

        if has_tool_tip:
            self.mesh_list_widget.setToolTip(tool_tip_text)
        self.mesh_list = mesh_list
        self.meshes_changed.emit(mesh_list)

    def on_select_mesh_button_pressed(self):
        mesh_picker = MeshListPicker(self, self.event_handler, self.allow_multi_select)
        if mesh_picker.exec_() == QtWidgets.QDialog.Accepted:
            mesh_list = mesh_picker.get_selected_meshes()
            if mesh_list:
                self.set_meshes(mesh_list)

    def on_add_selected_mesh_button_pressed(self):
         mesh_list = self.event_handler.get_selected_mesh_list()
         if mesh_list: 
             self.set_meshes(mesh_list)
