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

from PyQt5.QtWidgets import QApplication, QComboBox, QStyledItemDelegate, QDialog, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QSpacerItem, QSizePolicy, QHeaderView, QLabel, QWidget, QCheckBox, QHBoxLayout, QMessageBox, QFormLayout, QLineEdit
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
            self.result = self.op_func()
            self.op_updated.emit(self.result)
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
        
        file_path = os.path.join(encontrar_directorio_de_marcador("resources"), "resources", "fingerprint.ico")
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

        self.label_no_fallido = QLabel("No hay dispositivo activo", self)
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
        header_labels = ["IP", "Punto de Marcación", "Nombre de Distrito", "ID", "Cant. de Marcaciones"]
        super().__init__(parent, gestionar_marcaciones_dispositivos, "Obtener marcaciones", header_labels)
        self.__init_ui_son()

    def __init_ui_son(self):
        button_layout = QHBoxLayout()

        self.btn_retry_all_connection = QPushButton("Reintentar todos", self)
        self.btn_retry_all_connection.clicked.connect(self.on_retry_all_connection_clicked)
        button_layout.addWidget(self.btn_retry_all_connection)
        self.btn_retry_all_connection.setVisible(False)  # Ocultar el botón después de hacer clic

        self.btn_retry_failed_connection = QPushButton("Reintentar fallidos", self)
        self.btn_retry_failed_connection.clicked.connect(self.on_retry_failed_connection_clicked)
        button_layout.addWidget(self.btn_retry_failed_connection)
        self.btn_retry_failed_connection.setVisible(False)  # Ocultar el botón después de hacer clic

        self.layout().addLayout(button_layout)

        self.setLayout(self.layout())

        self.label_total_marcaciones = QLabel("Total de Marcaciones: 0", self)
        self.label_total_marcaciones.setAlignment(Qt.AlignCenter)
        self.layout().addWidget(self.label_total_marcaciones)
        self.label_total_marcaciones.setVisible(False)

    def update_table(self, device_status=None):
        self.total_marcaciones = 0
        super().update_table(device_status)
        self.show_btn_retry_failed_connection()
        self.label_total_marcaciones.setText(f"Total de Marcaciones: {self.total_marcaciones}")
        self.label_total_marcaciones.setVisible(True)

    def show_btn_retry_failed_connection(self):
        self.btn_actualizar.setVisible(False)
        self.btn_retry_all_connection.setVisible(True)
        
        has_failed_connection = any(
            device["cant_marcaciones"] == "Conexión fallida" for device in self.op_thread.result.values()
            )
        if has_failed_connection:
            self.btn_retry_failed_connection.setVisible(True)

    def update_last_column(self, row, device_info):
        status_item = QTableWidgetItem(device_info.get("cant_marcaciones", ""))
        if device_info.get("cant_marcaciones") == "Conexión fallida":
            status_item.setBackground(QColor(Qt.red))
        else:
            status_item.setBackground(QColor(Qt.green))
        
        self.table_widget.setItem(row, 4, status_item)
        try:
            self.total_marcaciones += int(device_info.get("cant_marcaciones", 0))
            logging.debug(f'Total attendances: {self.total_marcaciones}')
        except ValueError:
            pass
    
    def on_retry_all_connection_clicked(self):
        self.label_total_marcaciones.setVisible(False)

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
    
        self.btn_retry_failed_connection.setVisible(False)  # Ocultar el botón después de hacer clic
        self.btn_retry_all_connection.setVisible(False)  # Ocultar el botón después de hacer clic
    
    def on_retry_failed_connection_clicked(self):
        self.label_total_marcaciones.setVisible(False)

        try:
            with open('info_devices.txt', 'r') as file:
                lines = file.readlines()

            new_lines = []
            for line in lines:
                parts = line.strip().split(' - ')
                ip = parts[3]
                if ip in self.op_thread.result and self.op_thread.result[ip]["cant_marcaciones"] == "Conexión fallida":
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
    
        self.btn_retry_all_connection.setVisible(False)  # Ocultar el botón después de hacer clic
        self.btn_retry_failed_connection.setVisible(False)  # Ocultar el botón después de hacer clic

class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        # Crear y configurar un nuevo QComboBox para la celda
        combo_box = QComboBox(parent)
        combo_box.addItem("UDP")
        combo_box.addItem("TCP")
        return combo_box

    def setEditorData(self, editor, index):
        # Establecer el valor del QComboBox según los datos del modelo
        value = index.data()
        if value is not None:
            editor.setCurrentText(value)

    def setModelData(self, editor, model, index):
        # Guardar el valor seleccionado del QComboBox en el modelo
        model.setData(index, editor.currentText())

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
        
        file_path = os.path.join(encontrar_directorio_de_marcador("resources"), "resources", "fingerprint.ico")
        self.setWindowIcon(QIcon(file_path))
        
        self.file_path = os.path.join(encontrar_directorio_raiz(), "info_devices.txt")
        self.data = []
        self.max_id = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(7)
        self.table_widget.setHorizontalHeaderLabels(["Distrito", "Modelo", "Punto de Marcación", "IP", "ID", "Comunicación", "Activado"])
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

        self.btn_activate_all = QPushButton("Activar todo", self)
        self.btn_activate_all.clicked.connect(self.activate_all)
        button_layout.addWidget(self.btn_activate_all)

        self.btn_deactivate_all = QPushButton("Desactivar todo", self)
        self.btn_deactivate_all.clicked.connect(self.deactivate_all)
        button_layout.addWidget(self.btn_deactivate_all)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Clear focus from buttons
        self.btn_load_data.setAutoDefault(False)
        self.btn_load_data.setDefault(False)
        self.btn_save_data.setAutoDefault(False)
        self.btn_save_data.setDefault(False)
        self.btn_add_data.setAutoDefault(False)
        self.btn_add_data.setDefault(False)
        self.btn_activate_all.setAutoDefault(False)
        self.btn_activate_all.setDefault(False)
        self.btn_deactivate_all.setAutoDefault(False)
        self.btn_deactivate_all.setDefault(False)

        self.load_data_and_show()

    # Métodos para la lógica de selección y deselección de casillas "Activo"
    def activate_all(self):
        for row in range(self.table_widget.rowCount()):
            checkbox_delegate = self.table_widget.cellWidget(row, 6)
            checkbox_delegate.setChecked(True)

    def deactivate_all(self):
        for row in range(self.table_widget.rowCount()):
            checkbox_delegate = self.table_widget.cellWidget(row, 6)
            checkbox_delegate.setChecked(False)

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
                    if len(parts) == 7:
                        distrito, modelo, punto_marcacion, ip, id, comunicacion, activado = parts
                        self.max_id = max(self.max_id, int(id))  # Update max_id
                        data.append((distrito, modelo, punto_marcacion, ip, id, comunicacion, activado == 'True'))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar datos: {e}")
        return data

    def load_data_into_table(self):
        self.table_widget.setRowCount(0)
        for row, (distrito, modelo, punto_marcacion, ip, id, comunicacion, activado) in enumerate(self.data):
            self.table_widget.insertRow(row)
            self.table_widget.setItem(row, 0, QTableWidgetItem(distrito))
            self.table_widget.setItem(row, 1, QTableWidgetItem(modelo))
            self.table_widget.setItem(row, 2, QTableWidgetItem(punto_marcacion))
            self.table_widget.setItem(row, 3, QTableWidgetItem(ip))
            self.table_widget.setItem(row, 4, QTableWidgetItem(str(id)))
            # Configurar ComboBoxDelegate para la columna 5
            combo_box_delegate = ComboBoxDelegate(self.table_widget)
            self.table_widget.setItemDelegateForColumn(5, combo_box_delegate)
            # Establecer el valor en el modelo para la columna 5
            self.table_widget.setItem(row, 5, QTableWidgetItem(comunicacion))
            # Configurar CheckBoxDelegate para la columna 6
            checkbox_delegate = CheckBoxDelegate()
            checkbox_delegate.setChecked(activado)
            self.table_widget.setCellWidget(row, 6, checkbox_delegate)

    def save_data(self):
        try:
            with open(self.file_path, 'w') as file:
                for row in range(self.table_widget.rowCount()):
                    distrito = self.table_widget.item(row, 0).text().upper()
                    modelo = self.table_widget.item(row, 1).text()
                    punto_marcacion = self.table_widget.item(row, 2).text().upper()
                    ip = self.table_widget.item(row, 3).text()
                    id = self.table_widget.item(row, 4).text()
                    comunicacion = self.table_widget.item(row, 5).text()
                    activado = self.table_widget.cellWidget(row, 6).isChecked()
                    logging.debug(f"{distrito} - {modelo} - {punto_marcacion} - {ip} - {id} - {comunicacion} - {activado}")
                    file.write(f"{distrito} - {modelo} - {punto_marcacion} - {ip} - {id} - {comunicacion} - {activado}\n")
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
        # Crear un QComboBox
        self.combo_box = QComboBox()
        # Agregar elementos al QComboBox
        self.combo_box.addItem("TCP")
        self.combo_box.addItem("UDP")
        # Conectar la señal del QComboBox a un slot
        self.combo_box.currentIndexChanged.connect(self.on_combobox_changed)
        self.activado = True

        form_layout.addRow("Distrito:", self.distrito_edit)
        form_layout.addRow("Modelo:", self.modelo_edit)
        form_layout.addRow("Punto de Marcación:", self.punto_marcacion_edit)
        form_layout.addRow("IP:", self.ip_edit)
        form_layout.addRow("Comunicación:", self.combo_box)

        layout.addLayout(form_layout)

        self.btn_add = QPushButton("Agregar", self)
        self.btn_add.clicked.connect(self.accept)
        layout.addWidget(self.btn_add)

        self.setLayout(layout)
        
    def on_combobox_changed(self, index):
        # Obtener el texto de la opción seleccionada
        self.comunicacion = self.combo_box.currentText()

    def get_data(self):
        return (
            self.distrito_edit.text().upper(),
            self.modelo_edit.text(),
            self.punto_marcacion_edit.text().upper(),
            self.ip_edit.text(),
            self.id,
            self.comunicacion,
            self.activado
        )