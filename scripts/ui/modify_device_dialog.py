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

import logging
import os
from scripts.ui.base_dialog import BaseDialog
from scripts.ui.checkbox import CheckBoxDelegate
from scripts.ui.combobox import ComboBoxDelegate
from scripts.utils.file_manager import find_root_directory
from PyQt5.QtWidgets import QMessageBox, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QVBoxLayout, QPushButton, QDialog, QHBoxLayout, QComboBox, QFormLayout, QLineEdit, QCheckBox, QComboBox, QHeaderView

class ModifyDevicesDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent, window_title="Modificar dispositivos")
                
        self.file_path = os.path.join(find_root_directory(), "info_devices.txt")
        self.data = []
        self.max_id = 0
        self.init_ui()
        super().init_ui()

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

    # Methods for selecting and deselecting "Active" checkboxes
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
        dialog = AddDevicesDialog(self, new_id)
        if dialog.exec() == QDialog.Accepted:
            new_device_data = dialog.get_data()
            logging.debug(new_device_data)
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
                        district, model, point, ip, id, communication, active = parts
                        self.max_id = max(self.max_id, int(id))  # Update max_id
                        data.append((district, model, point, ip, id, communication, active == 'True'))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar datos: {e}")
        return data

    def load_data_into_table(self):
        self.table_widget.setRowCount(0)
        for row, (district, model, point, ip, id, communication, active) in enumerate(self.data):
            self.table_widget.insertRow(row)
            self.table_widget.setItem(row, 0, QTableWidgetItem(district))
            self.table_widget.setItem(row, 1, QTableWidgetItem(model))
            self.table_widget.setItem(row, 2, QTableWidgetItem(point))
            self.table_widget.setItem(row, 3, QTableWidgetItem(ip))
            self.table_widget.setItem(row, 4, QTableWidgetItem(str(id)))
            # Set ComboBoxDelegate for column 5
            combo_box_delegate = ComboBoxDelegate(self.table_widget)
            self.table_widget.setItemDelegateForColumn(5, combo_box_delegate)
            # Set the value in the model for column 5
            self.table_widget.setItem(row, 5, QTableWidgetItem(communication))
            # Set CheckBoxDelegate for column 6
            checkbox_delegate = CheckBoxDelegate()
            checkbox_delegate.setChecked(active)
            self.table_widget.setCellWidget(row, 6, checkbox_delegate)

    def save_data(self):
        try:
            with open(self.file_path, 'w') as file:
                for row in range(self.table_widget.rowCount()):
                    district = self.table_widget.item(row, 0).text().upper()
                    model = self.table_widget.item(row, 1).text()
                    point = self.table_widget.item(row, 2).text().upper()
                    ip = self.table_widget.item(row, 3).text()
                    id = self.table_widget.item(row, 4).text()
                    communication = self.table_widget.item(row, 5).text()
                    active = self.table_widget.cellWidget(row, 6).isChecked()
                    logging.debug(f"{district} - {model} - {point} - {ip} - {id} - {communication} - {active}")
                    file.write(f"{district} - {model} - {point} - {ip} - {id} - {communication} - {active}\n")
            QMessageBox.information(self, "Éxito", "Datos guardados correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar datos: {e}")

class AddDevicesDialog(QDialog):
    def __init__(self, parent=None, id=0):
        super().__init__(parent)
        self.setWindowTitle("Agregar nuevo dispositivo")
        self.setMinimumSize(400, 300)
        self.id = id
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        
        self.district_edit = QLineEdit(self)
        self.model_edit = QLineEdit(self)
        self.point_edit = QLineEdit(self)
        self.ip_edit = QLineEdit(self)
        # Create a QComboBox
        self.combo_box = QComboBox()
        # Add items to the QComboBox
        self.combo_box.addItem("TCP")
        self.combo_box.addItem("UDP")
        # Connect the QComboBox signal to a slot
        self.combo_box.currentIndexChanged.connect(self.on_combobox_changed)
        self.communication = self.combo_box.currentText()
        
        self.active = True

        form_layout.addRow("Distrito:", self.district_edit)
        form_layout.addRow("Modelo:", self.model_edit)
        form_layout.addRow("Punto de Marcación:", self.point_edit)
        form_layout.addRow("IP:", self.ip_edit)
        form_layout.addRow("Comunicación:", self.combo_box)
        
        layout.addLayout(form_layout)

        self.btn_add = QPushButton("Agregar", self)
        self.btn_add.clicked.connect(self.accept)
        layout.addWidget(self.btn_add)

        self.setLayout(layout)
        
    def on_combobox_changed(self, index):
        # Get the text of the selected option
        self.communication = self.combo_box.currentText()
        logging.debug(self.communication)

    def get_data(self):
        return (
            self.district_edit.text().upper(),
            self.model_edit.text(),
            self.point_edit.text().upper(),
            self.ip_edit.text(),
            self.id,
            self.communication,
            self.active
        )