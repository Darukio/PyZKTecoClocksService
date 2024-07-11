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
from PyQt5.QtGui import QColor, QIcon
from device_manager import ping_devices  # Importa la función para hacer ping a dispositivos
from utils import logging
from attendances_manager import obtener_cantidad_marcaciones_dispositivos, gestionar_marcaciones_dispositivos
import os

class PingThread(QThread):
    ping_updated = pyqtSignal(dict)

    def __init__(self, op_func, parent=None):
        super().__init__(parent)
        self.op_func = op_func

    def run(self):
        try:
            #from icon_manager import iniciar_cronometro, finalizar_cronometro
            #tiempo_inicial = iniciar_cronometro()  # Iniciar el cronómetro
            result = self.op_func()
            #finalizar_cronometro(tiempo_inicial)  # Finalizar el cronómetro y mostrar notificación
            self.ping_updated.emit(result)
        except Exception as e:
            logging.critical(e)

# Definición de la clase base común
class DeviceDialogBase(QDialog):
    def __init__(self, parent=None, ping_function=None, window_title="", header_labels=None):
        super().__init__(parent)
        self.setWindowTitle(window_title)
        self.setMinimumSize(600, 400)
        
        # Icono de la ventana
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "energiademisiones.ico")
        self.setWindowIcon(QIcon(file_path))
        
        self.ping_thread = PingThread(ping_function)
        self.ping_thread.ping_updated.connect(self.update_table)
        
        self.init_ui(header_labels)
        
    def init_ui(self, header_labels):
        layout = QVBoxLayout(self)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels(header_labels)
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.setSortingEnabled(True)  # Permitir ordenamiento por clic en los encabezados de las columnas

        layout.addWidget(self.table_widget)

        # Etiqueta para "Actualizando datos"
        self.label_actualizando = QLabel("Actualizando datos...", self)
        self.label_actualizando.setAlignment(Qt.AlignCenter)
        self.label_actualizando.setVisible(False)  # Inicialmente invisible
        layout.addWidget(self.label_actualizando)

        # Etiqueta para "Sin conexiones fallidas"
        self.label_no_fallido = QLabel("Sin conexiones fallidas", self)
        self.label_no_fallido.setAlignment(Qt.AlignCenter)
        self.label_no_fallido.setVisible(False)  # Inicialmente invisible
        layout.addWidget(self.label_no_fallido)

        # Botón "Actualizar"
        self.btn_actualizar = QPushButton("Actualizar", self)
        self.btn_actualizar.clicked.connect(self.update_data)
        layout.addWidget(self.btn_actualizar, alignment=Qt.AlignCenter)

    def update_data(self):
        self.label_no_fallido.setVisible(False)
        self.label_actualizando.setVisible(True)  # Mostrar mensaje de "Actualizando datos"
        self.table_widget.setSortingEnabled(False)
        self.table_widget.setRowCount(0)  # Limpiar tabla antes de actualizar
        self.ping_thread.start()  # Iniciar el hilo para obtener datos

    def update_table(self, device_status=None):
        self.label_actualizando.setVisible(False)  # Ocultar mensaje de "Actualizando datos"
        logging.debug(device_status)

        if not device_status:
            self.label_no_fallido.setVisible(True)
            return

        for row, (ip, device_info) in enumerate(device_status.items()):
            self.table_widget.insertRow(row)
            self.table_widget.setItem(row, 0, QTableWidgetItem(ip))  # IP

            # Resto de la información del dispositivo
            self.table_widget.setItem(row, 1, QTableWidgetItem(device_info.get("punto_marcacion", "")))
            self.table_widget.setItem(row, 2, QTableWidgetItem(device_info.get("nombre_distrito", "")))
            self.table_widget.setItem(row, 3, QTableWidgetItem(device_info.get("id", "")))

            # Dependiendo de la subclase, podemos definir cómo mostrar el último elemento
            self.update_last_column(row, device_info)

        self.table_widget.setSortingEnabled(True)
        self.table_widget.sortByColumn(4, Qt.AscendingOrder)

    def update_last_column(self, row, device_info):
        raise NotImplementedError("Subclasses should implement this method")

    def reject(self):
        self.ping_thread.terminate()  # Detener el hilo cuando se cierra la ventana
        super().reject()


# Subclase para el diálogo de estado de dispositivos
class DeviceStatusDialog(DeviceDialogBase):
    def __init__(self, parent=None):
        header_labels = ["IP", "Punto de Marcación", "Nombre de Distrito", "ID", "Estado"]
        super().__init__(parent, ping_devices, "Probar conexiones", header_labels)

    def update_last_column(self, row, device_info):
        status_item = QTableWidgetItem(device_info.get("status", ""))
        if device_info.get("status") == "Conexión fallida":
            status_item.setBackground(QColor(Qt.red))
        else:
            status_item.setBackground(QColor(Qt.green))
        
        self.table_widget.setItem(row, 4, status_item)

# Subclase para el diálogo de estado de dispositivos
class DeviceAttendancesDialog(DeviceDialogBase):
    def __init__(self, parent=None):
        header_labels = ["IP", "Punto de Marcación", "Nombre de Distrito", "ID", "Estado"]
        super().__init__(parent, gestionar_marcaciones_dispositivos, "Obtener marcaciones", header_labels)

    def update_last_column(self, row, device_info):
        status_item = QTableWidgetItem(device_info.get("status", ""))
        if device_info.get("status") == "Conexión fallida":
            status_item.setBackground(QColor(Qt.red))
        else:
            status_item.setBackground(QColor(Qt.green))
        
        self.table_widget.setItem(row, 4, status_item)


# Subclase para el diálogo de cantidad de marcaciones
class DeviceAttendancesCountDialog(DeviceDialogBase):
    def __init__(self, parent=None):
        header_labels = ["IP", "Punto de Marcación", "Nombre de Distrito", "ID", "Cant. de Marcaciones"]
        super().__init__(parent, obtener_cantidad_marcaciones_dispositivos, "Obtener cantidad de marcaciones", header_labels)

    def update_last_column(self, row, device_info):
        status_item = QTableWidgetItem(device_info.get("cant_marcaciones", ""))
        if device_info.get("cant_marcaciones") == "Conexión fallida":
            status_item.setBackground(QColor(Qt.red))
        else:
            status_item.setBackground(QColor(Qt.green))
        
        self.table_widget.setItem(row, 4, status_item)