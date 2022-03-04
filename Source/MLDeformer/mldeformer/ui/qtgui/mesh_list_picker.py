# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

from PySide2 import QtWidgets

from mldeformer.ui.event_handler import EventHandler


class MeshListPicker(QtWidgets.QDialog):
    def __init__(self, parent, event_handler, allow_multi_select=True):
        super(MeshListPicker, self).__init__(parent)
        self.setModal(True)

        self.event_handler = event_handler
        self.selected_meshes = list()

        if allow_multi_select:
            self.setWindowTitle('Choose one or more meshes')
        else:
            self.setWindowTitle('Choose a mesh')

        self.resize(400, 400)
        self.main_widget = QtWidgets.QWidget(self)
        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)

        header_label = QtWidgets.QLabel('Please select from the following list of meshes:')
        self.main_layout.addWidget(header_label)

        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        if allow_multi_select:
            self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.main_layout.addWidget(self.list_widget)

        # Fill the list widget with meshes.
        mesh_list = self.event_handler.get_mesh_list()
        for item in mesh_list:
            self.list_widget.addItem(item)

        # Create an OK button.
        ok_button = QtWidgets.QPushButton('Ok')
        ok_button.clicked.connect(self.on_ok_button_pressed)
        self.main_layout.addWidget(ok_button)

    def get_selected_meshes(self):
        return self.selected_meshes

    def update_selecte_meshes(self):
        selected_items = self.list_widget.selectedItems()
        del self.selected_meshes[:]
        for item in selected_items:
            self.selected_meshes.append(item.text())

    def on_ok_button_pressed(self):
        self.update_selecte_meshes()
        self.accept()

    def on_item_double_clicked(self):
        self.update_selecte_meshes()
        self.accept()
