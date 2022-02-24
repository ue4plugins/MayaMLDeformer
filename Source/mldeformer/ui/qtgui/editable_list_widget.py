# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

from mldeformer.ui.event_handler import EventHandler
from mldeformer.ui.qtgui.list_widget import ListWidget


class EditableListWidget(QtWidgets.QWidget):
    def __init__(self, event_handler, initial_string_list=list()):
        super(EditableListWidget, self).__init__()
        self.string_list = initial_string_list
        self.item_being_edited = None
        self.default_new_item_string = '<new item>'
        self.event_handler = event_handler

        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        self.list_widget = ListWidget()
        self.list_widget.setSortingEnabled(False)
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.list_widget.itemSelectionChanged.connect(self.on_item_selection_changed)
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.main_layout.addWidget(self.list_widget)

        button_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addLayout(button_layout)
        filler_widget = QtWidgets.QWidget()
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.MinimumExpanding)
        filler_widget.setSizePolicy(size_policy)
        self.add_button = QtWidgets.QPushButton(QtGui.QIcon(self.event_handler.add_icon_path), '')
        self.add_button.setFixedSize(20, 20)
        self.add_button.clicked.connect(self.on_add_button_pressed)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.add_button.setSizePolicy(size_policy)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(filler_widget)

        self.setMaximumHeight(100)

    def clear(self, trigger_contents_changed=True):
        self.list_widget.clear(trigger_contents_changed)

    def set_contents(self, item_list):
        self.clear(trigger_contents_changed=False)
        for item in item_list:
            self.list_widget.add_item(item_text=item, trigger_contents_changed=False, update_selection=False)

    def on_add_button_pressed(self):
        if self.item_being_edited:
            self.list_widget.closePersistentEditor(self.item_being_edited)

        item = QtWidgets.QListWidgetItem(self.default_new_item_string, self.list_widget)

        self.list_widget.clear_selection()
        item.setSelected(True)
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.list_widget.editItem(item)
        self.item_being_edited = item

    def on_item_selection_changed(self):
        if self.item_being_edited:
            if len(self.item_being_edited.text()) == 0:
                self.list_widget.closePersistentEditor(self.item_being_edited)
                self.list_widget.takeItem(self.list_widget.row(self.item_being_edited))
            else:
                self.list_widget.closePersistentEditor(self.item_being_edited)
            self.item_being_edited = None

    def on_item_double_clicked(self, item):
        if self.item_being_edited and item is not self.item_being_edited:
            self.list_widget.closePersistentEditor(self.item_being_edited)
            self.item_being_edited = None
            self.list_widget.clear_selection()
            item.setSelected(True)

        self.list_widget.editItem(item)
        self.item_being_edited = item
