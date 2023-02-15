# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

from PySide2 import QtWidgets

from mldeformer.ui.event_handler import EventHandler

from mldeformer.ui.qtgui.helpers import QtHelpers
from mldeformer.ui.qtgui.mesh_field_widget import MeshFieldWidget

from PySide2 import QtCore


class EditMeshMappingDialog(QtWidgets.QDialog):
    min_label_text_width = 120
    ok_pressed = QtCore.Signal(list)

    def __init__(self, parent, event_handler, base_mesh_name='', target_mesh_name=''):
        super(EditMeshMappingDialog, self).__init__(parent)

        self.setWindowTitle('Configure Mesh Mapping')
        self.setModal(False)
        self.base_mesh_name = base_mesh_name
        self.target_mesh_name = target_mesh_name
        self.event_handler = event_handler
        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)

        self.mesh_grid_layout = QtWidgets.QGridLayout()
        self.mesh_group = QtWidgets.QGroupBox('Mesh Mapping')
        self.mesh_group.setStyleSheet('QGroupBox::title { color: orange }')
        self.main_layout.addWidget(self.mesh_group)
        self.mesh_grid_layout.setColumnStretch(0, 0)
        self.mesh_grid_layout.setColumnStretch(1, 1)
        self.mesh_group.setLayout(self.mesh_grid_layout)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.mesh_group.setSizePolicy(size_policy)

        self.base_mesh_widget = MeshFieldWidget(
            event_handler=self.event_handler,
            allow_multi_select=False,
            is_optional=False,
            place_holder_text='<base mesh>')
        base_mesh_list = list()
        if base_mesh_name:
            base_mesh_list.append(base_mesh_name)
        self.base_mesh_widget.set_meshes(base_mesh_list)
        QtHelpers.add_widget_field(self.mesh_grid_layout, row_index=0, name='Base Mesh:', widget=self.base_mesh_widget,
                                   min_label_text_width=self.min_label_text_width,
                                   label_alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        self.target_mesh_widget = MeshFieldWidget(
            event_handler=self.event_handler,
            allow_multi_select=False,
            is_optional=True,
            place_holder_text='<target mesh>')
        target_mesh_list = list()
        if target_mesh_name:
            target_mesh_list.append(target_mesh_name)
        self.target_mesh_widget.set_meshes(target_mesh_list)
        QtHelpers.add_widget_field(self.mesh_grid_layout, row_index=1, name='Target Mesh:',
                                   widget=self.target_mesh_widget,
                                   min_label_text_width=self.min_label_text_width,
                                   label_alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        # Connect the settings widgets so we can capture the changes.
        self.base_mesh_widget.meshes_changed.connect(self.on_base_mesh_changed)
        self.target_mesh_widget.meshes_changed.connect(self.on_target_mesh_changed)

        self.ok_button = QtWidgets.QPushButton('Ok')
        self.ok_button.setEnabled(len(self.base_mesh_name) > 0)
        self.ok_button.clicked.connect(self.on_ok_button_pressed)
        self.main_layout.addWidget(self.ok_button)

        self.main_layout.addStretch(1)
        self.resize(500, self.height())

    def on_ok_button_pressed(self):
        if not self.base_mesh_widget.mesh_list:
            return
        self.accept()

    def on_base_mesh_changed(self, mesh_list):
        self.base_mesh_name = mesh_list[0]
        if not self.base_mesh_name:
            self.ok_button.setEnabled(False)
        else:
            self.ok_button.setEnabled(True)

    def on_target_mesh_changed(self, mesh_list):
        self.target_mesh_name = mesh_list[0]
