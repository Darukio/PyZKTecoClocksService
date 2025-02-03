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

# Subclass for the device status dialog
import logging
from scripts.business_logic.attendances_manager import manage_device_attendances
from scripts.ui.device_base_dialog import DeviceBaseDialog
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QLabel, QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

class DeviceAttendancesDialog(DeviceBaseDialog):
    def __init__(self, parent=None):
        header_labels = ["IP", "Punto de Marcación", "Nombre de Distrito", "ID", "Cant. de Marcaciones"]
        super().__init__(parent, manage_device_attendances, "Obtener marcaciones", header_labels)
        self.btn_update.setText("Obtener marcaciones")
        self.__init_ui_son()
        self.op_thread.progress_updated.connect(self.update_progress)  # Connect the progress signal

    def __init_ui_son(self):
        try:
            button_layout = QHBoxLayout()

            self.btn_retry_all_connection = QPushButton("Reintentar todos", self)
            self.btn_retry_all_connection.clicked.connect(self.on_retry_all_connection_clicked)
            button_layout.addWidget(self.btn_retry_all_connection)
            self.btn_retry_all_connection.setVisible(False)

            self.btn_retry_failed_connection = QPushButton("Reintentar fallidos", self)
            self.btn_retry_failed_connection.clicked.connect(self.on_retry_failed_connection_clicked)
            button_layout.addWidget(self.btn_retry_failed_connection)
            self.btn_retry_failed_connection.setVisible(False)

            self.layout().addLayout(button_layout)

            self.setLayout(self.layout())

            self.label_total_marcaciones = QLabel("Total de Marcaciones: 0", self)
            self.label_total_marcaciones.setAlignment(Qt.AlignCenter)
            self.layout().addWidget(self.label_total_marcaciones)
            self.label_total_marcaciones.setVisible(False)
        except Exception as e:
            logging.error(f"Error al inicializar la ventana de marcaciones de dispositivos: {e}")

    def update_progress(self, percent_progress, device_progress, processed_devices, total_devices):
        if percent_progress and device_progress:
            self.progress_bar.setValue(percent_progress)  # Update the progress bar value
            self.label_actualizando.setText(f"Último intento de conexión: {device_progress}\n{processed_devices}/{total_devices} dispositivos")
        
    def update_table(self, device_status=None):
        try:
            self.total_marcaciones = 0
            super().update_table(device_status)
            self.show_btn_retry_failed_connection()
            self.label_total_marcaciones.setText(f"Total de Marcaciones: {self.total_marcaciones}")
            self.label_total_marcaciones.setVisible(True)
        except Exception as e:
            logging.error(f"Error al actualizar la tabla de dispositivos: {e}")

    def show_btn_retry_failed_connection(self):
        self.btn_retry_all_connection.setVisible(True)
        
        has_failed_connection = any(
            device["attendance_count"] == "Conexión fallida" for device in self.op_thread.result.values()
            )
        if has_failed_connection:
            self.btn_retry_failed_connection.setVisible(True)

    def update_last_column(self, row, device_info):
        try:
            status_item = QTableWidgetItem(device_info.get("attendance_count", ""))
            if device_info.get("attendance_count") == "Conexión fallida":
                status_item.setBackground(QColor(Qt.red))
            else:
                status_item.setBackground(QColor(Qt.green))
            
            self.table_widget.setItem(row, 4, status_item)
            try:
                self.total_marcaciones += int(device_info.get("attendance_count", 0))
                logging.debug(f'Total attendances: {self.total_marcaciones}')
            except ValueError:
                pass
        except Exception as e:
            logging.error(f"Error al actualizar la última columna de la tabla de dispositivos: {e}")
    
    def on_retry_all_connection_clicked(self):
        self.label_total_marcaciones.setVisible(False)
        self.label_actualizando.setText("Reintentando conexiones...")

        try:
            with open('info_devices.txt', 'r') as file:
                lines = file.readlines()

            new_lines = []
            for line in lines:
                parts = line.strip().split(' - ')
                ip = parts[3]
                parts[6] = "True"
                new_lines.append(' - '.join(parts) + '\n')

            with open('info_devices.txt', 'w') as file:
                file.writelines(new_lines)

            logging.debug("Estado activo actualizado correctamente.")

            self.update_data()
        except Exception as e:
            logging.error(f"Error al actualizar el estado activo: {e}")
    
        self.btn_retry_failed_connection.setVisible(False)  # Hide the button after clicking
        self.btn_retry_all_connection.setVisible(False)  # Hide the button after clicking
    
    def on_retry_failed_connection_clicked(self):
        self.label_total_marcaciones.setVisible(False)
        self.label_actualizando.setText("Reintentando conexiones...")

        try:
            with open('info_devices.txt', 'r') as file:
                lines = file.readlines()

            new_lines = []
            for line in lines:
                parts = line.strip().split(' - ')
                ip = parts[3]
                if ip in self.op_thread.result and self.op_thread.result[ip]["attendance_count"] == "Conexión fallida":
                    parts[6] = "True"
                else:
                    parts[6] = "False"
                new_lines.append(' - '.join(parts) + '\n')

            with open('info_devices.txt', 'w') as file:
                file.writelines(new_lines)

            logging.debug("Estado activo actualizado correctamente.")

            self.update_data()
        except Exception as e:
            logging.error(f"Error al actualizar el estado activo: {e}")
    
        self.btn_retry_all_connection.setVisible(False)  # Hide the button after clicking
        self.btn_retry_failed_connection.setVisible(False)  # Hide the button after clicking