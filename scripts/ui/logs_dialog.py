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

import os
import re
import json
from PyQt5.QtWidgets import (
    QVBoxLayout, QTextEdit, QDateEdit, QPushButton, QLabel, 
    QHBoxLayout, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import QDate
from scripts.ui.base_dialog import BaseDialog
from scripts.utils.errors import BaseErrorWithMessageBox
from PyQt5.QtGui import QIcon
from ..utils.file_manager import find_marker_directory, find_root_directory

LOGS_DIR = os.path.join(find_root_directory(), "logs")

# Load error codes from errors.json
ERROR_CODES_DICT = {}
ERROR_CODES_SET = set()

errors_file = os.path.join(find_marker_directory("json"), "json", "errors.json")
if os.path.exists(errors_file):
    with open(errors_file, encoding="utf-8", errors="replace") as f:
        ERROR_CODES_DICT = json.load(f)  # Dictionary of error codes and descriptions
        ERROR_CODES_SET = set(ERROR_CODES_DICT.keys())  # Set of error codes

class LogsDialog(BaseDialog):
    def __init__(self):
        super().__init__(window_title="Visor de Logs")
        self.init_ui()
        super().init_ui()

    def init_ui(self):
        try:
            # Date selection widgets
            self.start_date_edit = QDateEdit(self)
            self.start_date_edit.setCalendarPopup(True)
            self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
            self.start_date_edit.editingFinished.connect(self.load_logs)  # Dynamic filtering on date change

            self.end_date_edit = QDateEdit(self)
            self.end_date_edit.setCalendarPopup(True)
            self.end_date_edit.setDate(QDate.currentDate())
            self.end_date_edit.editingFinished.connect(self.load_logs)  # Dynamic filtering on date change

            # Error selection list (initially hidden)
            self.error_list = QListWidget(self)
            self.error_list.setSelectionMode(QListWidget.MultiSelection)
            self.error_list.setVisible(False)  # Initially hide the error list
            self.error_list.itemSelectionChanged.connect(self.load_logs)  # Dynamic filtering on selection change

            for code, description in ERROR_CODES_DICT.items():
                item = QListWidgetItem(f"[{code}] {description}")
                item.setData(1, code)  # Store only the error code as data
                self.error_list.addItem(item)

            # Button to toggle the error list visibility with an SVG icon
            self.toggle_filter_button = QPushButton(self)
            self.file_path_filter = os.path.join(self.file_path_resources, "window", "filter-right.svg")
            self.toggle_filter_button.setIcon(QIcon(self.file_path_filter))  # Set SVG icon
            self.toggle_filter_button.clicked.connect(self.toggle_error_list)

            self.select_errors_label = QLabel("Selecciona los errores a filtrar (vacío = todos):")
            self.select_errors_label.setVisible(False)

            # Layout for filters
            filter_layout = QHBoxLayout()
            filter_layout.addWidget(QLabel("Desde:"))
            filter_layout.addWidget(self.start_date_edit)
            filter_layout.addWidget(QLabel("Hasta:"))
            filter_layout.addWidget(self.end_date_edit)
            filter_layout.addWidget(self.toggle_filter_button)  # Button to toggle the error list

            # Text widget to display logs
            self.text_edit = QTextEdit(self)
            self.text_edit.setReadOnly(True)

            # Main layout
            layout = QVBoxLayout()
            layout.addLayout(filter_layout)
            layout.addWidget(self.select_errors_label)
            layout.addWidget(self.error_list)
            layout.addWidget(self.text_edit)
            self.setLayout(layout)

            # Load logs at startup
            self.load_logs()
        except Exception as e:
            BaseErrorWithMessageBox(3003, str(e))

    def toggle_error_list(self):
        """Toggle the visibility of the error list."""
        self.select_errors_label.setVisible(not self.select_errors_label.isVisible())
        self.error_list.setVisible(not self.error_list.isVisible())

    def load_logs(self):
        """Load error logs filtered by date and selected error codes."""
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

        selected_errors = {item.data(1) for item in self.error_list.selectedItems()}
        
        error_logs = self.get_error_logs(start_date, end_date, selected_errors)
        self.text_edit.setPlainText("\n".join(error_logs))

    def get_error_logs(self, start_date, end_date, selected_errors):
        """Retrieve error logs within the date range, filtered by selected errors."""
        error_entries = []
        pattern = re.compile(r"(\d{4}-\d{2}-\d{2}).* - \w+ - \[(\d{4})\]")  # Capture date and error code

        for folder in os.listdir(LOGS_DIR):
            folder_path = os.path.join(LOGS_DIR, folder)
            log_path = os.path.join(folder_path, "program_error.log")

            if os.path.isdir(folder_path) and os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8", errors="replace") as log_file:
                    for line in log_file:
                        match = pattern.search(line)
                        if match:
                            log_date, error_code = match.groups()
                            if start_date <= log_date <= end_date:
                                # Show all errors if none are selected, otherwise filter
                                if not selected_errors or error_code in selected_errors:
                                    error_entries.append(line.strip())

        return error_entries
