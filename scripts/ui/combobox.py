"""
    PyZKTecoClocks: GUI for managing ZKTeco clocks, enabling clock 
    time synchronization and attendance data retrieval.
    Copyright (C) 2024  Paulo Sebastian Spaciuk (Darukio)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from PyQt5.QtWidgets import QStyledItemDelegate, QComboBox

class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        # Create and configure a new QComboBox for the cell
        combo_box = QComboBox(parent)
        combo_box.addItem("UDP")
        combo_box.addItem("TCP")
        return combo_box

    def setEditorData(self, editor, index):
        # Set the value of the QComboBox according to the model data
        value = index.data()
        if value is not None:
            editor.setCurrentText(value)

    def setModelData(self, editor, model, index):
        # Save the selected value of the QComboBox in the model
        model.setData(index, editor.currentText())