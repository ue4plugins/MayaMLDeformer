# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

from mldeformer.ui.event_handler import EventHandler
from mldeformer.ui.attribute_minmax import AttributeMinMax
from mldeformer.ui.qtgui.helpers import QtHelpers


class ParamMinMaxSetupWindow(QtWidgets.QDialog):
    table_column__name = 0
    table_column__minimum = 1
    table_column__maximum = 2

    min_label_text_width = 75
    main_button_size = 22

    def __init__(self, parent, event_handler):
        super(ParamMinMaxSetupWindow, self).__init__(parent)

        self.event_handler = event_handler
        self.red_brush = QtGui.QBrush(QtGui.QColor(255, 80, 0))
        self.table_default_foreground_brush = QtGui.QBrush(QtGui.QColor(200, 200, 200))

        self.setWindowTitle('Attribute Min/Max Setup')
        self.resize(800, 400)
        self.main_widget = QtWidgets.QWidget(self)
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        # ----------------------------------------------------------
        # Create the left side contents widget.
        self.left_widget = QtWidgets.QWidget(self)
        self.left_layout = QtWidgets.QVBoxLayout(self.left_widget)

        # Create the parameters label bar.
        parameters_layout = QtWidgets.QHBoxLayout()
        self.left_layout.addLayout(parameters_layout)
        self.parameters_label = QtWidgets.QLabel('Attributes')
        self.parameters_label.setStyleSheet('color: orange')
        parameters_layout.addWidget(self.parameters_label)
        filler_widget = QtWidgets.QWidget()
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        filler_widget.setSizePolicy(size_policy)
        parameters_layout.addWidget(filler_widget)

        self.add_parameter_button = QtWidgets.QPushButton(QtGui.QIcon(self.event_handler.add_icon_path), '')
        self.add_parameter_button.setStyleSheet('background-color: green')
        self.add_parameter_button.setFixedSize(self.main_button_size, self.main_button_size)
        self.add_parameter_button.clicked.connect(self.on_add_button_pressed)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.add_parameter_button.setSizePolicy(size_policy)
        parameters_layout.addWidget(self.add_parameter_button)

        # Create the parameters table.
        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.on_table_context_menu)
        self.table.itemSelectionChanged.connect(self.on_table_selection_changed)
        self.left_layout.addWidget(self.table)
        self.table.setHorizontalHeaderLabels(['Attribute Name', 'Min', 'Max'])
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self.table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)

        # ----------------------------------------------------------
        # Create the right side of the UI.
        self.right_widget = QtWidgets.QWidget()
        self.right_layout = QtWidgets.QVBoxLayout(self.right_widget)

        # Create the properties group.
        self.hierarchy_properties_group = QtWidgets.QGroupBox('Attribute Settings')
        self.hierarchy_properties_group.setStyleSheet('QGroupBox::title { color: orange }')
        self.right_layout.addWidget(self.hierarchy_properties_group)
        self.hierarchy_filter_grid_layout = QtWidgets.QGridLayout()

        _, self.attribute_name_line_edit = QtHelpers.add_string_field(layout=self.hierarchy_filter_grid_layout,
                                                                      row_index=0,
                                                                      name='Name:', value='',
                                                                      min_label_text_width=self.min_label_text_width)
        _, self.min_value_widget = QtHelpers.add_float_field(layout=self.hierarchy_filter_grid_layout, row_index=1,
                                                             name='Minimum:', value=0.0, decimals=3,
                                                             min_value=-100000000.0,
                                                             max_value=100000000.0,
                                                             min_label_text_width=self.min_label_text_width)
        _, self.max_value_widget = QtHelpers.add_float_field(layout=self.hierarchy_filter_grid_layout, row_index=2,
                                                             name='Maximum:', value=1.0, decimals=3,
                                                             min_value=-100000000.0,
                                                             max_value=100000000.0,
                                                             min_label_text_width=self.min_label_text_width)

        self.attribute_name_line_edit.textChanged.connect(self.on_attribute_changed)
        self.min_value_widget.valueChanged.connect(self.on_attribute_changed)
        self.max_value_widget.valueChanged.connect(self.on_attribute_changed)

        self.hierarchy_properties_group.setLayout(self.hierarchy_filter_grid_layout)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.hierarchy_properties_group.setSizePolicy(size_policy)

        # ----------------------------------------------------------
        # Add an info group.
        self.info_group = QtWidgets.QGroupBox('')
        self.info_group.setStyleSheet('QGroupBox::title { color: orange }')
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.info_group.setSizePolicy(size_policy)
        self.right_layout.addWidget(self.info_group)

        self.info_layout = QtWidgets.QVBoxLayout()
        self.info_group.setLayout(self.info_layout)
        self.info_label = QtWidgets.QLabel(
            '<b><font color="#BBBBBB">Configure attribute min and max values.</font></b><br>'
            '<br>'
            'These values are ignored when:'
            '<ul style="margin-left:-20px">'
            '<li> The specific attribute is inside the attribute<br>'
            'ignore list when adding parameters.<br></li>'
            '<li> The specific attribute inside the DCC<br>'
            'already has min and max values setup.</li>'
            '</ul>'
        )
        self.info_label.setStyleSheet('color: rgb(135, 135, 135)')
        self.info_layout.addWidget(self.info_label)

        # ----------------------------------------------------------
        # Add a filler to fill the bottom of the right side.
        filler_widget = QtWidgets.QWidget()
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)
        filler_widget.setSizePolicy(size_policy)
        self.right_layout.addWidget(filler_widget)

        # ----------------------------------------------------------
        # Create the splitter.
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)
        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.right_widget)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        self.splitter.setSizes([600, 200])

        # Add the items to the table.
        self.init_table()

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.table.selectRow(0)
        self.on_table_selection_changed()

    # Get a list of selected attribute indices.
    def get_selected_attribute_indices(self):
        resulting_indices = list()
        selected_items = self.table.selectedItems()
        col_count = self.table.columnCount()
        num_selected_rows = int(len(selected_items) / col_count)
        assert (len(selected_items) % col_count) == 0, 'Expected entire row to be selected'
        for i in range(0, num_selected_rows):
            item = selected_items[i * col_count + self.table_column__name]
            index = item.data(QtCore.Qt.UserRole)
            resulting_indices.append(index)
        return resulting_indices

    def on_add_button_pressed(self):
        self.on_attribute_changed()
        new_object = AttributeMinMax()
        new_object.name = '<unnamed attribute>'
        self.event_handler.attribute_min_max_values.append(new_object)
        self.init_table()
        self.table.selectRow(len(self.event_handler.attribute_min_max_values) - 1)
        self.attribute_name_line_edit.setFocus()
        self.attribute_name_line_edit.selectAll()

    def on_table_selection_changed(self):
        # Block signals, so we don't trigger OnAttributeChanged caused by the setValue calls on the widgets.
        self.attribute_name_line_edit.blockSignals(True)
        self.min_value_widget.blockSignals(True)
        self.max_value_widget.blockSignals(True)

        # Update widget values.
        selected_items = self.table.selectedItems()
        if len(selected_items) == 0:
            self.attribute_name_line_edit.setText('')
            self.min_value_widget.setValue(0.0)
            self.max_value_widget.setValue(1.0)
            self.attribute_name_line_edit.setEnabled(False)
            self.min_value_widget.setEnabled(False)
            self.max_value_widget.setEnabled(False)
        else:
            selected_attributes = self.get_selected_attribute_indices()
            attribute = self.event_handler.attribute_min_max_values[selected_attributes[-1]]
            self.attribute_name_line_edit.setText(attribute.name)
            self.min_value_widget.setValue(attribute.min_value)
            self.max_value_widget.setValue(attribute.max_value)
            self.attribute_name_line_edit.setEnabled(True)
            self.min_value_widget.setEnabled(True)
            self.max_value_widget.setEnabled(True)

        # Unblock signals.
        self.attribute_name_line_edit.blockSignals(False)
        self.min_value_widget.blockSignals(False)
        self.max_value_widget.blockSignals(False)

    def on_attribute_changed(self):
        selected_items = self.table.selectedItems()
        if len(selected_items) == 0:
            return

        attribute_indices = self.get_selected_attribute_indices()
        if len(attribute_indices) == 1:
            attribute = self.event_handler.attribute_min_max_values[attribute_indices[0]]
            attribute.name = self.attribute_name_line_edit.text()

        for index in attribute_indices:
            attribute = self.event_handler.attribute_min_max_values[index]
            attribute.min_value = self.min_value_widget.value()
            attribute.max_value = self.max_value_widget.value()

        self.event_handler.save_attribute_min_max_setup_to_file(self.event_handler.min_max_settings_file)
        self.init_table()

    # Remove a given list of attributes, where the remove list is a list of indices.
    def remove_attributes_by_index_list(self, remove_list):
        for index in sorted(remove_list, reverse=True):
            self.table.removeRow(index)
            del self.event_handler.attribute_min_max_values[index]

        self.event_handler.save_attribute_min_max_setup_to_file(self.event_handler.min_max_settings_file)

        # Init the table again, which stores the user data attribute indices correctly again.
        self.init_table()

    # Remove all selected attributes.
    def remove_selected_attributes(self):
        remove_list = self.get_selected_attribute_indices()
        self.remove_attributes_by_index_list(remove_list)

    # Remove all attributes, clearing the table.
    def remove_all_attributes(self):
        remove_list = list(range(0, len(self.event_handler.attribute_min_max_values)))
        self.remove_attributes_by_index_list(remove_list)

    def on_table_context_menu(self, point):
        if self.table.rowCount() == 0:
            return

        menu = QtWidgets.QMenu(self)
        selected_indices = self.get_selected_attribute_indices()
        remove_selected_action = None
        if len(selected_indices) > 0:
            remove_selected_action = menu.addAction('Remove selected attributes')

        if selected_indices:
            menu.addSeparator()

        clear_action = menu.addAction('Clear')

        # Spawn the context menu and handle the action that was picked in the context menu.
        action = menu.exec_(self.mapToGlobal(point))
        if action:
            if remove_selected_action and action == remove_selected_action:
                self.remove_selected_attributes()
            elif action == clear_action:
                self.remove_all_attributes()

        self.table.clearSelection()

    def on_clear_table(self):
        self.remove_all_attributes()

    # Some key got pressed.
    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Delete:
            self.remove_selected_attributes()

    # Update the table colors for a given parameter.
    def update_colors(self, index):
        # Get the table widget items.
        name_item = self.table.item(index, self.table_column__name)
        min_value_item = self.table.item(index, self.table_column__minimum)
        max_value_item = self.table.item(index, self.table_column__maximum)

        # Init at default colors.
        name_item.setForeground(self.table_default_foreground_brush)
        min_value_item.setForeground(self.table_default_foreground_brush)
        max_value_item.setForeground(self.table_default_foreground_brush)

        if self.event_handler.has_min_max_item_errors(index):
            min_value_item.setForeground(self.red_brush)
            max_value_item.setForeground(self.red_brush)

    def init_table(self):
        self.table.setRowCount(len(self.event_handler.attribute_min_max_values))
        for row, attribute in enumerate(self.event_handler.attribute_min_max_values):
            name_item = QtWidgets.QTableWidgetItem(attribute.name)
            name_item.setData(QtCore.Qt.UserRole, row)
            self.table.setItem(row, self.table_column__name, name_item)
            self.table.setItem(row, self.table_column__minimum, QtWidgets.QTableWidgetItem(str(attribute.min_value)))
            self.table.setItem(row, self.table_column__maximum, QtWidgets.QTableWidgetItem(str(attribute.max_value)))
            self.update_colors(row)

        self.table.resizeRowsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)

    def closeEvent(self, event):
        if self.event_handler.has_min_max_errors():
            event.ignore()
            message = \
                'It appears that one or more items have a minimum value that is larger than the maximum value.<br>' + \
                '<br>' + \
                'Please fix the items colored in <font color="#FF5000">red</font> first.'
            QtWidgets.QMessageBox.warning(self, 'Invalid setup', message, QtWidgets.QMessageBox.Ok)
            return

        self.deleteLater()
