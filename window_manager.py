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

import sys
from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QSpacerItem, QSizePolicy, QHeaderView, QLabel
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor
from device_manager import ping_devices  # Importa la función para hacer ping a dispositivos
from utils import logging

class PingThread(QThread):
    ping_updated = pyqtSignal(dict)

    def run(self):
        device_status = ping_devices()
        self.ping_updated.emit(device_status)


class DeviceStatusDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Estado de Dispositivos")
        self.setMinimumSize(600, 400)  # Tamaño mínimo recomendado
        self.ping_thread = PingThread()
        self.ping_thread.ping_updated.connect(self.update_table)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels(["IP", "Punto de Marcación", "Nombre de Distrito", "ID", "Estado"])
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)  # Hacer toda la tabla no editable
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  # Ajustar tamaño de columnas según contenido
        self.table_widget.horizontalHeader().setStretchLastSection(True)  # Estirar la última sección para llenar el espacio

        layout.addWidget(self.table_widget)

        # Etiqueta para "Actualizando datos"
        self.label_actualizando = QLabel("Actualizando datos...", self)
        self.label_actualizando.setAlignment(Qt.AlignCenter)
        self.label_actualizando.setVisible(False)  # Inicialmente invisible

        layout.addWidget(self.label_actualizando)

        # Botón "Actualizar"
        self.btn_actualizar = QPushButton("Actualizar", self)
        self.btn_actualizar.clicked.connect(self.update_data)
        layout.addWidget(self.btn_actualizar, alignment=Qt.AlignCenter)

    def update_data(self):
        # Mostrar mensaje de "Actualizando datos" en la tabla
        self.label_actualizando.setVisible(True)

        # Iniciar el hilo para obtener datos
        self.ping_thread.start()

    def update_table(self, device_status=None):
        self.label_actualizando.setVisible(False)
        logging.debug(device_status)

        if device_status is None:
            return

        self.table_widget.setRowCount(0)  # Limpiar tabla antes de actualizar
        for row, (ip, device_info) in enumerate(device_status.items()):
            self.table_widget.insertRow(row)
            self.table_widget.setItem(row, 0, QTableWidgetItem(ip))  # IP

            # Resto de la información del dispositivo
            self.table_widget.setItem(row, 1, QTableWidgetItem(device_info["punto_marcacion"]))
            self.table_widget.setItem(row, 2, QTableWidgetItem(device_info["nombre_distrito"]))
            self.table_widget.setItem(row, 3, QTableWidgetItem(device_info["id"]))

            # Estado
            status_item = QTableWidgetItem(device_info["status"])
            if device_info["status"] == "Conexión fallida":
                status_item.setBackground(QColor(Qt.red))
            elif device_info["status"] == "Conexión exitosa":
                status_item.setBackground(QColor(Qt.green))

            self.table_widget.setItem(row, 4, status_item)

        #self.table_widget.resizeColumnsToContents()  # Ajustar ancho de columnas automáticamente

    def reject(self):
        self.ping_thread.terminate()  # Detener el hilo cuando se cierra la ventana
        super().reject()
