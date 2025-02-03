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

# Subclass for the attendance count dialog
from scripts.business_logic.attendances_manager import get_device_attendance_count
from scripts.ui.device_base_dialog import DeviceBaseDialog
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

class DeviceAttendancesCountDialog(DeviceBaseDialog):
    def __init__(self, parent=None):
        header_labels = ["IP", "Punto de Marcación", "Nombre de Distrito", "ID", "Cant. de Marcaciones"]
        super().__init__(parent, get_device_attendance_count, "Obtener cantidad de marcaciones", header_labels)
        self.btn_update.setText("Obtener cant. de marcaciones")

    def update_last_column(self, row, device_info):
        status_item = QTableWidgetItem(device_info.get("attendance_count", ""))
        if device_info.get("attendance_count") == "Conexión fallida":
            status_item.setBackground(QColor(Qt.red))
        else:
            status_item.setBackground(QColor(Qt.green))
        
        self.table_widget.setItem(row, 4, status_item)