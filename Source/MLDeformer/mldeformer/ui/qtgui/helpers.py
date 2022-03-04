# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

from PySide2 import QtCore
from PySide2 import QtWidgets


class QtHelpers:
    @staticmethod
    def center_window(window):
        rect = window.frameGeometry()
        center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
        rect.moveCenter(center_point)
        window.move(rect.topLeft())

    @staticmethod
    def add_float_field(layout, row_index, name, value, decimals=3, min_value=-100000000.0, max_value=100000000.0,
                        step_size=0.1, min_label_text_width=120):
        name_label = QtWidgets.QLabel(name)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        name_label.setSizePolicy(size_policy)
        name_label.setMinimumWidth(min_label_text_width)
        value_widget = QtWidgets.QDoubleSpinBox()
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        value_widget.setSizePolicy(size_policy)
        value_widget.setMinimumWidth(100)
        value_widget.setMaximumWidth(125)
        value_widget.setMinimum(min_value)
        value_widget.setMaximum(max_value)
        value_widget.setSingleStep(step_size)
        value_widget.setDecimals(decimals)
        value_widget.setValue(value)
        layout.addWidget(name_label, row_index, 0, QtCore.Qt.AlignRight)
        layout.addWidget(value_widget, row_index, 1, QtCore.Qt.AlignLeft)
        return name_label, value_widget

    @staticmethod
    def add_int_field(layout, row_index, name, value, min_value=-100000000, max_value=100000000,
                      min_label_text_width=120):
        name_label = QtWidgets.QLabel(name)
        name_label.setMinimumWidth(min_label_text_width)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        name_label.setSizePolicy(size_policy)
        value_widget = QtWidgets.QSpinBox()
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        value_widget.setSizePolicy(size_policy)
        value_widget.setMinimumWidth(100)
        value_widget.setMaximumWidth(125)
        value_widget.setMinimum(min_value)
        value_widget.setMaximum(max_value)
        value_widget.setValue(value)
        layout.addWidget(name_label, row_index, 0, QtCore.Qt.AlignRight)
        layout.addWidget(value_widget, row_index, 1, QtCore.Qt.AlignLeft)
        return name_label, value_widget

    @staticmethod
    def add_string_field(layout, row_index, name, value='', min_label_text_width=120):
        name_label = QtWidgets.QLabel(name)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        name_label.setSizePolicy(size_policy)
        name_label.setMinimumWidth(min_label_text_width)
        string_widget = QtWidgets.QLineEdit('')
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        string_widget.setSizePolicy(size_policy)
        string_widget.setMinimumWidth(175)
        string_widget.setText(value)
        layout.addWidget(name_label, row_index, 0, QtCore.Qt.AlignRight)
        layout.addWidget(string_widget, row_index, 1)
        return name_label, string_widget

    @staticmethod
    def add_check_box_field(layout, row_index, name, value=False, min_label_text_width=120):
        label = QtWidgets.QLabel(name)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        label.setSizePolicy(size_policy)
        label.setMinimumWidth(min_label_text_width)
        check_box = QtWidgets.QCheckBox()
        check_box.setChecked(value)
        layout.addWidget(label, row_index, 0, QtCore.Qt.AlignRight)
        layout.addWidget(check_box, row_index, 1)
        return label, check_box

    @staticmethod
    def add_combo_box_field(layout, row_index, name, combo_items, min_label_text_width=120):
        label = QtWidgets.QLabel(name)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        label.setSizePolicy(size_policy)
        label.setMinimumWidth(min_label_text_width)
        combo_box = QtWidgets.QComboBox()
        combo_box.addItems(combo_items)
        combo_box.setCurrentIndex(0)
        combo_box.setEditable(False)
        layout.addWidget(label, row_index, 0, QtCore.Qt.AlignRight)
        layout.addWidget(combo_box, row_index, 1)
        return label, combo_box

    @staticmethod
    def add_widget_field(layout, row_index, name, widget, min_label_text_width=120,
                         label_alignment=QtCore.Qt.AlignRight | QtCore.Qt.AlignTop):
        label = QtWidgets.QLabel(name)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        label.setSizePolicy(size_policy)
        label.setMinimumWidth(min_label_text_width)
        layout.addWidget(label, row_index, 0, label_alignment)
        layout.addWidget(widget, row_index, 1)
        return label, widget
