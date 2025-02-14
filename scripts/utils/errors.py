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

import json
import logging
import os
from PyQt5.QtWidgets import QMessageBox

from scripts.utils.file_manager import find_marker_directory

# Load errors from JSON
# with open(os.path.join(find_marker_directory("json"), "json", "errors.json"), encoding="utf-8") as f:
#    ERRORS = json.load(f)

ERRORS = {
    "0000": "Error desconocido",
    "1000": "Error al conectar con el dispositivo",
    "1001": "Error de red",
    "2000": "Error de dispositivo",
    "2001": "Error de pila fallando",
    "2002": "Error al reiniciar el dispositivo",
    "3000": "Error de aplicacion",
    "3001": "Error de carga de archivo",
    "3500": "Error de interfaz grafica",
    "3501": "Error al inicializar ventana",
}

class BaseError(Exception):
    """Base class for errors with logging support."""

    def __init__(self, error_code, extra_info="", level="error"):
        self.code = error_code
        self.message = ERRORS.get(str(error_code), 0000)
        
        if extra_info:
            self.message += f" ({extra_info})"

        log = f"[{self.code}] {self.message}"
        # Determine logging level
        if level == "warning":
            logging.warning(log)
        elif level == "error":
            logging.error(log)
        elif level == "critical":
            logging.critical(log)

        super().__init__(log)

class BaseErrorWithMessageBox(BaseError):
    """Base class for errors with logging and message box support."""

    def __init__(self, error_code, extra_info="", level="error"):
        super().__init__(error_code, extra_info, level)
        QMessageBox.critical(None, f"Error {self.code}", self.message)

# Error and warning classes
class ConnectionFailedError(BaseError):
    def __init__(self, extra_info=""):
        super().__init__(1000, extra_info, level="warning")

class NetworkError(BaseError):
    def __init__(self, model_name="", point="", ip=""):
        super().__init__(1001, f'{model_name} - {point} - {ip}')

class OutdatedTimeError(Exception):
    def __init__(self, ip=""):
        super().__init__(ip)

class BatteryFailingError(BaseError):
    def __init__(self, model_name="", point="", ip=""):
        self.ip = ip
        super().__init__(2001, f'{model_name} - {point} - {ip}')
