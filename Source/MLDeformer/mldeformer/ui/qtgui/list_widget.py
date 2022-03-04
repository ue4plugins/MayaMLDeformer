# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

from PySide2 import QtCore
from PySide2 import QtWidgets


class ListWidget(QtWidgets.QListWidget):
    contents_changed = QtCore.Signal()

    def __init__(self):
        super(ListWidget, self).__init__()

    def dataChanged(self, top_left, bottom_right, roles):
        self.emit_contents_changed()

    def emit_contents_changed(self):
        self.contents_changed.emit()

    def clear_selection(self):
        for i in range(self.count()):
            item = self.item(i)
            self.setItemSelected(item, False)

    def add_item(self, item_text, trigger_contents_changed=True, update_selection=True):
        existing_items = self.findItems(item_text, QtCore.Qt.MatchFixedString)
        if len(existing_items) > 0:
            return

        self.addItem(item_text)
        new_item = self.findItems(item_text, QtCore.Qt.MatchExactly)[0]
        new_item.setFlags(new_item.flags() | QtCore.Qt.ItemIsEditable)

        if update_selection:
            self.clear_selection()
            self.setCurrentItem(new_item)

        if trigger_contents_changed:
            self.emit_contents_changed()

    def clear(self, trigger_contents_changed=True):
        super(ListWidget, self).clear()
        if trigger_contents_changed:
            self.emit_contents_changed()

    # Handle delete key to remove selected items from the list.
    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Delete:
            list_items = self.selectedItems()
            if not list_items:
                return

            first_row_index = self.row(list_items[0])
            for item in list_items:
                self.takeItem(self.row(item))

            if self.count() > first_row_index:
                self.item(first_row_index).setSelected(True)
            else:
                if (first_row_index > 0) and (self.count() > first_row_index - 1):
                    self.item(first_row_index - 1).setSelected(True)

        self.emit_contents_changed()
