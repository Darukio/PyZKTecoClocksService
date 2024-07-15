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

from ..utils.errors import *
from ..utils.file_manager import *
from ..business_logic.attendances_manager import *
from ..business_logic.hour_manager import *
from ..business_logic.device_manager import ping_devices  # Importa la función para hacer ping a dispositivos
from scripts import config

from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QSpacerItem, QSizePolicy, QHeaderView, QLabel, QWidget, QCheckBox, QHBoxLayout, QMessageBox, QFormLayout, QLineEdit
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QIcon
import logging
import os
import sys

class OpThread(QThread):
    op_updated = pyqtSignal(dict)
    op_terminated = pyqtSignal(float)

    def __init__(self, op_func, parent=None):
        super().__init__(parent)
        self.op_func = op_func

    def run(self):
        try:
            import time
            tiempo_inicial = time.time()
            result = self.op_func()
            self.op_updated.emit(result)
            self.op_terminated.emit(tiempo_inicial)
        except Exception as e:
            logging.critical(e)

# Definición de la clase base común
class DeviceDialogBase(QDialog):
    op_terminated = pyqtSignal(float)

    def __init__(self, parent=None, op_function=None, window_title="", header_labels=None):
        super().__init__(parent)
        self.setWindowTitle(window_title)
        self.setMinimumSize(600, 400)
        
        file_path = os.path.join(encontrar_directorio_raiz(os.path.abspath(__file__)), "resources", "fingerprint.ico")
        self.setWindowIcon(QIcon(file_path))
        
        self.op_thread = OpThread(op_function)
        self.op_thread.op_updated.connect(self.update_table)
        self.op_thread.op_terminated.connect(self.terminate_op)
        
        self.init_ui(header_labels)
    
    def terminate_op(self, tiempo_inicial):
        logging.debug(f'tiempo inicial: {tiempo_inicial}')
        self.op_terminated.emit(tiempo_inicial)
    
    def init_ui(self, header_labels):
        layout = QVBoxLayout(self)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels(header_labels)
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.setSortingEnabled(True)

        layout.addWidget(self.table_widget)

        self.btn_actualizar = QPushButton("Actualizar", self)
        self.btn_actualizar.clicked.connect(self.update_data)
        layout.addWidget(self.btn_actualizar, alignment=Qt.AlignCenter)

        self.label_actualizando = QLabel("Actualizando datos...", self)
        self.label_actualizando.setAlignment(Qt.AlignCenter)
        self.label_actualizando.setVisible(False)
        layout.addWidget(self.label_actualizando)

        self.label_no_fallido = QLabel("Sin conexiones fallidas", self)
        self.label_no_fallido.setAlignment(Qt.AlignCenter)
        self.label_no_fallido.setVisible(False)
        layout.addWidget(self.label_no_fallido)

    def update_data(self):
        self.label_no_fallido.setVisible(False)
        self.label_actualizando.setVisible(True)
        self.table_widget.setSortingEnabled(False)
        self.table_widget.setRowCount(0)
        self.op_thread.start()

    def update_table(self, device_status=None):
        self.label_actualizando.setVisible(False)
        logging.debug(device_status)

        if not device_status:
            self.label_no_fallido.setVisible(True)
            return

        for row, (ip, device_info) in enumerate(device_status.items()):
            self.table_widget.insertRow(row)
            self.table_widget.setItem(row, 0, QTableWidgetItem(ip))
            self.table_widget.setItem(row, 1, QTableWidgetItem(device_info.get("punto_marcacion", "")))
            self.table_widget.setItem(row, 2, QTableWidgetItem(device_info.get("nombre_distrito", "")))
            self.table_widget.setItem(row, 3, QTableWidgetItem(device_info.get("id", "")))
            self.update_last_column(row, device_info)

        self.table_widget.setSortingEnabled(True)
        self.table_widget.sortByColumn(4, Qt.AscendingOrder)

    def update_last_column(self, row, device_info):
        raise NotImplementedError("Subclasses should implement this method")

    def reject(self):
        self.op_thread.terminate()
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

class DeviceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Modificar dispositivos")
        self.setMinimumSize(600, 400)
        
        file_path = os.path.join(encontrar_directorio_raiz(os.path.abspath(__file__)), "resources", "fingerprint.ico")
        self.setWindowIcon(QIcon(file_path))
        
        self.file_path = os.path.join(encontrar_directorio_raiz(os.path.abspath(__file__)), "info_devices.txt")
        self.data = []
        self.max_id = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(6)
        self.table_widget.setHorizontalHeaderLabels(["Distrito", "Modelo", "Punto de Marcación", "IP", "ID", "Activado"])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.setEditTriggers(QTableWidget.DoubleClicked)

        layout.addWidget(self.table_widget)

        button_layout = QHBoxLayout()

        self.btn_load_data = QPushButton("Cargar", self)
        self.btn_load_data.clicked.connect(self.load_data_and_show)
        button_layout.addWidget(self.btn_load_data)

        self.btn_save_data = QPushButton("Modificar", self)
        self.btn_save_data.clicked.connect(self.save_data)
        button_layout.addWidget(self.btn_save_data)

        self.btn_add_data = QPushButton("Agregar", self)
        self.btn_add_data.clicked.connect(self.add_device)
        button_layout.addWidget(self.btn_add_data)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Clear focus from buttons
        self.btn_load_data.setAutoDefault(False)
        self.btn_load_data.setDefault(False)
        self.btn_save_data.setAutoDefault(False)
        self.btn_save_data.setDefault(False)
        self.btn_add_data.setAutoDefault(False)
        self.btn_add_data.setDefault(False)        

        self.load_data_and_show()

    def add_device(self):
        new_id = self.max_id + 1  # Calculate new ID
        dialog = AddDeviceDialog(self, new_id)
        if dialog.exec() == QDialog.Accepted:
            new_device_data = dialog.get_data()
            self.data.append(new_device_data)
            self.max_id = new_id  # Update max_id
            self.load_data_into_table()

    def load_data_and_show(self):
        self.data = self.load_data()
        self.load_data_into_table()

    def load_data(self):
        data = []
        try:
            with open(self.file_path, 'r') as file:
                for line in file:
                    parts = line.strip().split(' - ')
                    if len(parts) == 6:
                        distrito, modelo, punto_marcacion, ip, id, activado = parts
                        self.max_id = max(self.max_id, int(id))  # Update max_id
                        data.append((distrito, modelo, punto_marcacion, ip, id, activado == 'True'))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar datos: {e}")
        return data

    def load_data_into_table(self):
        self.table_widget.setRowCount(0)
        for row, (distrito, modelo, punto_marcacion, ip, id, activado) in enumerate(self.data):
            self.table_widget.insertRow(row)
            self.table_widget.setItem(row, 0, QTableWidgetItem(distrito))
            self.table_widget.setItem(row, 1, QTableWidgetItem(modelo))
            self.table_widget.setItem(row, 2, QTableWidgetItem(punto_marcacion))
            self.table_widget.setItem(row, 3, QTableWidgetItem(ip))
            self.table_widget.setItem(row, 4, QTableWidgetItem(str(id)))
            checkbox_delegate = CheckBoxDelegate()
            checkbox_delegate.setChecked(activado)
            self.table_widget.setCellWidget(row, 5, checkbox_delegate)

    def save_data(self):
        try:
            with open(self.file_path, 'w') as file:
                for row in range(self.table_widget.rowCount()):
                    distrito = self.table_widget.item(row, 0).text().upper()
                    modelo = self.table_widget.item(row, 1).text()
                    punto_marcacion = self.table_widget.item(row, 2).text().upper()
                    ip = self.table_widget.item(row, 3).text()
                    id = self.table_widget.item(row, 4).text()
                    activado = self.table_widget.cellWidget(row, 5).isChecked()
                    logging.debug(f"{distrito} - {modelo} - {punto_marcacion} - {ip} - {id} - {activado}")
                    file.write(f"{distrito} - {modelo} - {punto_marcacion} - {ip} - {id} - {activado}\n")
            QMessageBox.information(self, "Éxito", "Datos guardados correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar datos: {e}")

class CheckBoxDelegate(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.checkbox = QCheckBox(self)
        layout.addWidget(self.checkbox)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def isChecked(self):
        return self.checkbox.isChecked()

    def setChecked(self, state):
        self.checkbox.setChecked(state)

class AddDeviceDialog(QDialog):
    def __init__(self, parent=None, id=0):
        super().__init__(parent)
        self.setWindowTitle("Agregar nuevo dispositivo")
        self.setMinimumSize(400, 300)
        self.id = id
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        
        self.distrito_edit = QLineEdit(self)
        self.modelo_edit = QLineEdit(self)
        self.punto_marcacion_edit = QLineEdit(self)
        self.ip_edit = QLineEdit(self)
        self.activado = True

        form_layout.addRow("Distrito:", self.distrito_edit)
        form_layout.addRow("Modelo:", self.modelo_edit)
        form_layout.addRow("Punto de Marcación:", self.punto_marcacion_edit)
        form_layout.addRow("IP:", self.ip_edit)

        layout.addLayout(form_layout)

        self.btn_add = QPushButton("Agregar", self)
        self.btn_add.clicked.connect(self.accept)
        layout.addWidget(self.btn_add)

        self.setLayout(layout)

    def get_data(self):
        return (
            self.distrito_edit.text().upper(),
            self.modelo_edit.text(),
            self.punto_marcacion_edit.text().upper(),
            self.ip_edit.text(),
            self.id,
            self.activado
        )