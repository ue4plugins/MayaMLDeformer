# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved
from PySide2 import QtGui
from PySide2 import QtCore
from PySide2 import QtWidgets


class TableWidget(QtWidgets.QTableWidget):
    copy_rows = QtCore.Signal()
    paste_rows = QtCore.Signal()

    def __init__(self, rows, columns):
        super(TableWidget, self).__init__(rows, columns)
        self.copied_index = None

    def keyPressEvent(self, event):
        if event == QtGui.QKeySequence.Copy:
            if self.currentIndex().isValid():
                self.copied_index = self.currentIndex().row()
                if not event.isAutoRepeat():
                    self.copy_rows.emit()
            else:
                self.copied_index = None
        elif event == QtGui.QKeySequence.Paste:
            if not event.isAutoRepeat() and self.copied_index is not None:
                self.paste_rows.emit()
        else:
            super(TableWidget, self).keyPressEvent(event)
