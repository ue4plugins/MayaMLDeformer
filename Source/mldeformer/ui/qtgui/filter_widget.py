# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

from PySide2 import QtCore
from PySide2 import QtWidgets


class FilterWidget(QtWidgets.QWidget):
    text_changed = QtCore.Signal(str)

    def __init__(self, fixed_height_value=5):
        super(FilterWidget, self).__init__(None)

        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)

        self.label = QtWidgets.QLabel('Filter: ')
        self.label.setFixedHeight(fixed_height_value)
        self.main_layout.addWidget(self.label)
        self.line_edit = QtWidgets.QLineEdit()
        self.line_edit.setPlaceholderText('Enter text')
        self.line_edit.setFixedHeight(fixed_height_value)
        self.main_layout.addWidget(self.line_edit)

        self.clear_button = QtWidgets.QPushButton('x')
        self.clear_button.setFixedSize(20, fixed_height_value)
        self.main_layout.addWidget(self.clear_button)

        self.line_edit.setStyleSheet(
            'QLineEdit { border-width: 1px 0px 1px 1px; border-style: solid; border-color: rgb(85,85,85) }')
        self.clear_button.setStyleSheet(
            'QPushButton { border-width: 1px 1px 1px 0px; border-style: solid; border-color: rgb(85,85,85); background: rgb(55,55,55)}')

        self.clear_button.clicked.connect(self.on_clear_button_clicked)
        self.line_edit.editingFinished.connect(self.on_text_changed)

    def on_clear_button_clicked(self):
        self.line_edit.setText('')
        self.on_text_changed()

    def on_text_changed(self):
        self.text_changed.emit(self.line_edit.text())
