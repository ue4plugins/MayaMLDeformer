# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

from mldeformer.ui.Qt import QtCore, QtGui, QtWidgets
from mldeformer.ui.qtgui.filter_widget import FilterWidget


class JointPickerWindow(QtWidgets.QDialog):
    def __init__(self, parent, event_handler, dimmed_names=None, dimmed_tooltip=''):
        super(JointPickerWindow, self).__init__(parent)

        self.proxy_model = None
        self.item_map = None
        self.root_items = None
        self.selected_items = list()
        self.dimmed_names = dimmed_names if dimmed_names else list()
        self.dimmed_tooltip = dimmed_tooltip
        self.joint_list = dict()
        self.event_handler = event_handler

        self.bottom_layout = None
        self.ok_button = None
        self.cancel_button = None
        self.joint_widget = None
        self.filter_widget = None
        self.filter_text = str()
        self.top_layout = None
        self.main_layout = None
        self.main_widget = None

        self.init_ui()

    def init_ui(self):
        # Create the main window.
        self.setObjectName('MLDeformerJointPickerWindow')
        self.setWindowTitle('Select Joints')
        self.setWindowIcon(QtGui.QIcon(self.event_handler.unreal_icon_path))
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.resize(550, 800)

        # Create the main widget and layout.
        self.main_layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.setLayout(self.main_layout)

        # Create the top layout for the filter.
        self.top_layout = QtWidgets.QHBoxLayout()
        self.main_layout.addLayout(self.top_layout)

        # Joint list label. 
        text_widget = QtWidgets.QLabel('Joint List:')
        text_widget.setStyleSheet('color: orange')
        self.top_layout.addWidget(text_widget)

        # Add a filler.
        filler_widget = QtWidgets.QWidget()
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        filler_widget.setSizePolicy(size_policy)
        self.top_layout.addWidget(filler_widget)

        # Create the search filter widget.
        self.filter_widget = FilterWidget(fixed_height_value=22)
        self.filter_widget.setMaximumWidth(400)
        self.filter_widget.text_changed.connect(self.on_filter_text_changed)
        self.top_layout.addWidget(self.filter_widget)

        # Add the joint list.
        self.joint_widget = QtWidgets.QTreeView()
        self.joint_widget.setHeaderHidden(True)
        self.joint_widget.setSortingEnabled(True)
        self.joint_widget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        standard_model = QtGui.QStandardItemModel()
        self.proxy_model = QtCore.QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(standard_model)
        self.proxy_model.setFilterKeyColumn(0)
        self.proxy_model.setDynamicSortFilter(True)
        self.proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setRecursiveFilteringEnabled(True)
        self.joint_widget.setModel(self.proxy_model)

        self.joint_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.create_joint_items()
        self.main_layout.addWidget(self.joint_widget)

        # Add the ok and cancel buttons.
        self.bottom_layout = QtWidgets.QHBoxLayout()
        self.main_layout.addLayout(self.bottom_layout)

        self.ok_button = QtWidgets.QPushButton('OK')
        self.ok_button.clicked.connect(self.on_ok_pressed)
        self.bottom_layout.addWidget(self.ok_button)

        self.cancel_button = QtWidgets.QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.on_cancel_pressed)
        self.bottom_layout.addWidget(self.cancel_button)

    def on_cancel_pressed(self):
        self.selected_items = list()
        self.reject()

    def on_ok_pressed(self):
        self.selected_items.clear()

        selected = self.joint_widget.selectionModel().selectedRows()
        if len(selected) > 0:
            remapped_selection = [self.joint_widget.model().mapToSource(index) for index in selected]
            self.selected_items = [self.joint_widget.model().sourceModel().itemFromIndex(index).text() for index in remapped_selection]

        self.accept()

    def on_filter_text_changed(self, new_text: str):
        self.proxy_model.setFilterFixedString(new_text)
        self.joint_widget.expandAll()

    def get_picked_joint_list(self) -> list:
        return self.selected_items

    def create_joint_items(self):
        joints = self.event_handler.get_joint_names()
        self.item_map = dict()
        self.root_items = list()
        for joint_name, parent in joints.items():
            item = QtGui.QStandardItem(joint_name)

            if joint_name in self.dimmed_names:
                item.setData(QtGui.QColor(100, 100, 100), QtCore.Qt.TextColorRole)
                item.setToolTip(self.dimmed_tooltip)

            self.item_map[joint_name] = item
            if not parent or parent not in joints:
                self.root_items.append(item)

        # Now add child items.
        for joint_name, parent_name in joints.items():
            item = self.item_map[joint_name]
            if parent_name and parent_name in self.item_map:
                parent_item = self.item_map[parent_name]
                parent_item.appendRow(item)

        if self.root_items:
            for item in self.root_items:
                self.joint_widget.model().sourceModel().appendRow(item)

        self.joint_widget.expandAll()
