# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

from mldeformer.ui.event_handler import EventHandler
from mldeformer.ui.qtgui.edit_mesh_mapping_dialog import EditMeshMappingDialog
from mldeformer.ui.mesh_mapping import MeshMapping


class MeshMappingWidget(QtWidgets.QWidget):
    contents_changed = QtCore.Signal()

    table_column__base_mesh_name = 0
    table_column__target_mesh_name = 1

    def __init__(self, event_handler):
        super(MeshMappingWidget, self).__init__(None)

        self.event_handler = event_handler
        self.error_text = ''
        self.mesh_mapping_dialog = None
        self.red_brush = QtGui.QBrush(QtGui.QColor(255, 80, 0))
        self.dark_red_brush = QtGui.QBrush(QtGui.QColor(128, 40, 0))
        self.dark_gray_brush = QtGui.QBrush(QtGui.QColor(95, 95, 95))
        self.table_default_foreground_brush = QtGui.QBrush(QtGui.QColor(200, 200, 200))

        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        # Create the parameters table.
        self.table = QtWidgets.QTableWidget(0, 2)
        self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.on_table_context_menu)
        self.table.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.main_layout.addWidget(self.table)
        self.table.setHorizontalHeaderLabels(['Base Mesh', 'Target Mesh'])
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self.table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)

        self.right_layout = QtWidgets.QVBoxLayout()
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(self.right_layout)

        self.add_button = QtWidgets.QPushButton(QtGui.QIcon(self.event_handler.add_icon_path), '')
        self.add_button.clicked.connect(self.on_add_button_pressed)
        self.add_button.setFixedSize(20, 20)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.add_button.setSizePolicy(size_policy)
        self.right_layout.addWidget(self.add_button)

        self.right_layout.addStretch(1)

        self.update()

    def on_item_double_clicked(self, item):
        mapping_index = item.data(QtCore.Qt.UserRole)
        self.edit_item(mapping_index)

    def sort_mappings(self):
        if self.event_handler.generator_config.mesh_mappings:
            self.event_handler.generator_config.mesh_mappings.sort(key=lambda x: x.base_mesh_name.lower())

    def edit_item(self, mapping_index):
        mapping = self.event_handler.generator_config.mesh_mappings[mapping_index]
        new_mapping_dialog = EditMeshMappingDialog(self, self.event_handler, mapping.base_mesh_name,
                                                   mapping.target_mesh_name)
        if new_mapping_dialog.exec_() == QtWidgets.QDialog.Accepted:
            mapping.base_mesh_name = new_mapping_dialog.base_mesh_name
            mapping.target_mesh_name = new_mapping_dialog.target_mesh_name
            self.sort_mappings()
            self.update()
            self.contents_changed.emit()

    # Some key got pressed.
    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Delete:
            self.remove_selected_mappings()

    # Remove a given list of mappings, where the remove list is a list of indices.
    def remove_mappings_by_index_list(self, remove_list):
        for index in sorted(remove_list, reverse=True):
            self.table.removeRow(index)
            del self.event_handler.generator_config.mesh_mappings[index]

        # Init the table again, which stores the user data indices correctly again.
        self.init_table()
        self.contents_changed.emit()

    # Remove all selected mappings.
    def remove_selected_mappings(self):
        remove_list = self.get_selected_mapping_indices()
        self.remove_mappings_by_index_list(remove_list)

    # Remove all mappings, clearing the table.
    def remove_all_mappings(self):
        remove_list = list(range(0, len(self.event_handler.generator_config.mesh_mappings)))
        self.remove_mappings_by_index_list(remove_list)

    # Get a list of selected mapping indices.
    def get_selected_mapping_indices(self):
        resulting_indices = list()
        selected_items = self.table.selectedItems()
        col_count = self.table.columnCount()
        num_selected_rows = len(selected_items) / col_count
        assert (len(selected_items) % col_count) == 0, 'Expected entire row to be selected.'
        for i in range(0, int(num_selected_rows)):
            item = selected_items[i * col_count + self.table_column__base_mesh_name]
            index = item.data(QtCore.Qt.UserRole)
            resulting_indices.append(index)
        return resulting_indices

    # We right clicked on the table.
    def on_table_context_menu(self, point):
        if self.table.rowCount() == 0:
            return

        menu = QtWidgets.QMenu(self)
        selected_indices = self.get_selected_mapping_indices()
        remove_selected_action = None
        edit_selected_action = None
        enable_action = None
        disable_action = None
        if selected_indices:
            if len(selected_indices) == 1:
                edit_selected_action = menu.addAction('Edit')
                menu.addSeparator()

            if any(
                not self.event_handler.generator_config.mesh_mappings[index].is_enabled for index in selected_indices):
                enable_action = menu.addAction('Enable')

            if any(self.event_handler.generator_config.mesh_mappings[index].is_enabled for index in selected_indices):
                disable_action = menu.addAction('Disable')

            menu.addSeparator()

            remove_selected_action = menu.addAction('Remove')

        if selected_indices:
            menu.addSeparator()

        clear_action = menu.addAction('Clear')

        # Spawn the context menu and handle the action that was picked in the context menu.
        action = menu.exec_(self.mapToGlobal(point))
        if action:
            if remove_selected_action and action == remove_selected_action:
                self.remove_selected_mappings()
            elif action == clear_action:
                self.remove_all_mappings()
            elif edit_selected_action and action == edit_selected_action:
                self.edit_item(selected_indices[0])
            elif disable_action and action == disable_action:
                for index in selected_indices:
                    self.event_handler.generator_config.mesh_mappings[index].is_enabled = False
                self.update()
                self.contents_changed.emit()
            elif enable_action and action == enable_action:
                for index in selected_indices:
                    self.event_handler.generator_config.mesh_mappings[index].is_enabled = True
                self.update()
                self.contents_changed.emit()

        self.table.clearSelection()

    def on_add_button_pressed(self):
        if not self.mesh_mapping_dialog:
            self.mesh_mapping_dialog = EditMeshMappingDialog(self, self.event_handler)
            self.mesh_mapping_dialog.finished.connect(self.on_mesh_mapping_finished)
        self.mesh_mapping_dialog.show()

    def on_mesh_mapping_finished(self, result):
        if result == QtWidgets.QDialog.Accepted:
            base_mesh_name = self.mesh_mapping_dialog.base_mesh_name
            target_mesh_name = self.mesh_mapping_dialog.target_mesh_name
            mapping_list = self.event_handler.generator_config.mesh_mappings
            duplicate = False
            for mapping in mapping_list:
                if mapping.base_mesh_name == base_mesh_name: 
                    duplicate = True

            if not duplicate:
                new_mapping = MeshMapping(base_mesh_name, target_mesh_name, enabled=True)
                self.event_handler.generator_config.mesh_mappings.append(new_mapping)
                self.sort_mappings()
                self.init_table()
                self.contents_changed.emit()

        self.mesh_mapping_dialog.close()
        self.mesh_mapping_dialog = None

    def update_error_text(self):
        mapping_list = self.event_handler.generator_config.mesh_mappings
        mesh_list = self.event_handler.get_mesh_list()

        self.error_text = ''
        missing_meshes = list()
        if mesh_list:
            for mapping in mapping_list:
                if not mapping.is_enabled:
                    continue

                if mapping.base_mesh_name not in mesh_list:
                    missing_meshes.append(mapping.base_mesh_name)

                if mapping.target_mesh_name and not (mapping.target_mesh_name in mesh_list):
                    missing_meshes.append(mapping.target_mesh_name)

            if missing_meshes:
                missing_meshes = list(set(missing_meshes))
                self.error_text += 'The following meshes are missing in the {} scene:<br>'.format(
                    self.event_handler.get_dcc_name())
            for mesh_name in missing_meshes:
                self.error_text += '<font color="yellow">{}</font><br>'.format(mesh_name)

    def update_table_colors(self, mapping_index):
        # Get the table widget items.
        base_name_item = self.table.item(mapping_index, self.table_column__base_mesh_name)
        target_name_item = self.table.item(mapping_index, self.table_column__target_mesh_name)

        # Init at default colors.
        mapping = self.event_handler.generator_config.mesh_mappings[mapping_index]

        mesh_list = self.event_handler.get_mesh_list()
        if mapping.is_enabled:
            base_name_item.setForeground(
                self.table_default_foreground_brush if mapping.base_mesh_name in mesh_list else self.red_brush)
            target_name_item.setForeground(
                self.table_default_foreground_brush if mapping.target_mesh_name in mesh_list else self.red_brush)
        else:
            base_name_item.setForeground(
                self.dark_gray_brush if mapping.base_mesh_name in mesh_list else self.dark_red_brush)
            target_name_item.setForeground(
                self.dark_gray_brush if mapping.target_mesh_name in mesh_list else self.dark_red_brush)

    def init_table(self):
        mappings = self.event_handler.generator_config.mesh_mappings

        if not mappings:
            self.table.setRowCount(0)
            self.table.horizontalHeader().setStretchLastSection(True)
            table_width = 250
            self.table.setColumnWidth(self.table_column__base_mesh_name, table_width / 2)
            self.table.setColumnWidth(self.table_column__target_mesh_name, table_width / 2)
            return

        self.table.setRowCount(len(mappings))
        for mapping_index, mapping in enumerate(mappings):
            base_name_item = QtWidgets.QTableWidgetItem(mapping.base_mesh_name)
            base_name_item.setData(QtCore.Qt.UserRole, mapping_index)
            self.table.setItem(mapping_index, self.table_column__base_mesh_name, base_name_item)

            target_name_item = QtWidgets.QTableWidgetItem(mapping.target_mesh_name)
            target_name_item.setData(QtCore.Qt.UserRole, mapping_index)
            self.table.setItem(mapping_index, self.table_column__target_mesh_name, target_name_item)

            self.update_table_colors(mapping_index)

        self.table.resizeRowsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)

    def update(self):
        self.init_table()
        self.update_error_text()
