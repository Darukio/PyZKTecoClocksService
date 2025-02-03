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

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QCheckBox, QPushButton, QHeaderView, QMessageBox
)
import os
import logging

from scripts.business_logic.connection import restart_device
from scripts.business_logic.device_manager import retry_network_operation
from scripts.ui.base_dialog import BaseDialog
from scripts.ui.combobox import ComboBoxDelegate
from PyQt5.QtCore import Qt

from scripts.utils.errors import BaseError, BaseErrorWithMessageBox, ConnectionFailedError

class RestartDevicesDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent, window_title="Reiniciar dispositivos")

        # Path to the file with device information
        self.file_path = os.path.join(os.getcwd(), "info_devices.txt")
        self.data = []
        self.init_ui()
        super().init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Table to display devices
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(7)
        self.table_widget.setHorizontalHeaderLabels(["Distrito", "Modelo", "Punto de Marcación", "IP", "ID", "Comunicación", "Seleccionar reinicio"])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_widget)

        # Button to restart selected devices
        self.btn_restart = QPushButton("Reiniciar dispositivos")
        self.btn_restart.clicked.connect(self.restart_selected_devices)
        layout.addWidget(self.btn_restart)

        self.setLayout(layout)

        # Load initial data
        self.load_data()

    def load_data(self):
        """Load devices from the file and display them in the table."""
        try:
            self.data = []
            with open(self.file_path, "r") as file:
                for line in file:
                    parts = line.strip().split(" - ")
                    if len(parts) == 7:
                        distrito, modelo, punto_marcacion, ip, id, comunicacion, activo = parts
                        self.data.append((distrito, modelo, punto_marcacion, ip, id, comunicacion))
            self.load_data_into_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la información: {e}")

    def load_data_into_table(self):
        """Fill the table with device data."""
        self.table_widget.setRowCount(0)

        for row, (distrito, modelo, punto_marcacion, ip, id, comunicacion) in enumerate(self.data):
            self.table_widget.insertRow(row)

            # Create non-editable cells
            item_distrito = QTableWidgetItem(distrito)
            item_distrito.setFlags(item_distrito.flags() & ~Qt.ItemIsEditable)
            self.table_widget.setItem(row, 0, item_distrito)

            item_modelo = QTableWidgetItem(modelo)
            item_modelo.setFlags(item_modelo.flags() & ~Qt.ItemIsEditable)
            self.table_widget.setItem(row, 1, item_modelo)

            item_punto_marcacion = QTableWidgetItem(punto_marcacion)
            item_punto_marcacion.setFlags(item_punto_marcacion.flags() & ~Qt.ItemIsEditable)
            self.table_widget.setItem(row, 2, item_punto_marcacion)

            item_ip = QTableWidgetItem(ip)
            item_ip.setFlags(item_ip.flags() & ~Qt.ItemIsEditable)
            self.table_widget.setItem(row, 3, item_ip)

            item_id = QTableWidgetItem(str(id))
            item_id.setFlags(item_id.flags() & ~Qt.ItemIsEditable)
            self.table_widget.setItem(row, 4, item_id)

            # Configure ComboBoxDelegate for column 5 but disable editing
            combo_box_delegate = ComboBoxDelegate(self.table_widget)
            self.table_widget.setItemDelegateForColumn(5, combo_box_delegate)

            # Display the value as text, not editable
            item_comunicacion = QTableWidgetItem(comunicacion)
            item_comunicacion.setFlags(item_comunicacion.flags() & ~Qt.ItemIsEditable)
            self.table_widget.setItem(row, 5, item_comunicacion)

            # Configure CheckBox in column 6 (interactive)
            checkbox = QCheckBox()
            checkbox.setChecked(False)
            self.table_widget.setCellWidget(row, 6, checkbox)

    def restart_selected_devices(self):
        """Restart selected devices."""
        selected_devices = []
        for row in range(self.table_widget.rowCount()):
            checkbox = self.table_widget.cellWidget(row, 6)
            if checkbox and checkbox.isChecked():
                ip = self.table_widget.item(row, 3).text()
                communication = self.table_widget.item(row, 5).text()
                selected_devices.append((ip, communication))

        if not selected_devices:
            QMessageBox.information(self, "Sin selección", "No se seleccionaron dispositivos para reiniciar.")
            return

        for ip, communication in selected_devices:

            try:
                retry_network_operation(restart_device, args=(ip, 4370, communication,))
                QMessageBox.information(self, "Éxito", "Dispositivos reiniciados correctamente.")
                logging.info(f"Dispositivo IP: {ip} reiniciado correctamente.")
            except ConnectionFailedError as e:
                BaseErrorWithMessageBox(2002, str(e))
            except Exception as e:
                BaseError(0000, str(e))