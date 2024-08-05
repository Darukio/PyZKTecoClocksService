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

import eventlet
eventlet.monkey_patch()
from PyQt5.QtWidgets import QApplication
from scripts.ui.icon_manager import MainWindow
from scripts.utils.logging import config_log, logging
from scripts.utils.file_manager import encontrar_directorio_raiz
import sys
import os
import configparser
import threading

# Versión del programa
VERSION = "v2.4.2-beta"

# Para leer un archivo INI
from scripts import config
config.read(os.path.join(encontrar_directorio_raiz(), 'config.ini'))

def main():
    config_log()

    import os
    logging.debug('Script executing...')

    MODE = 'User' if getattr(sys, 'frozen', False) else 'Developer'
    msg_init = f"Program version: {VERSION} - Mode: {MODE}"
    logging.info(msg_init)
    print(msg_init)
    print_copyright()

    config_log_console()
    config_content()

    if len(sys.argv) == 1:
        try:
            app = QApplication(sys.argv)
            main_window = MainWindow()
            sys.exit(app.exec_())
            
        except Exception as e:
            logging.error(e)

def config_content():
    for section in config.sections():
        logging.debug(f'Section: {section}')
        # Iterar sobre las claves y valores dentro de cada sección
        for key, value in config.items(section):
            logging.debug(f'Subsection: {key}, Value: {value}')

def config_log_console():
    log_file_path = os.path.join(encontrar_directorio_raiz(), 'logs', 'console_log.txt')
    logging.debug(encontrar_directorio_raiz())
    logging.debug(sys.executable)
    
    # Asegúrate de que el archivo de log y su directorio existen
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    if not os.path.exists(log_file_path):
        with open(log_file_path, 'w') as f:
            pass  # Crear el archivo si no existe

    # Redirigir salida estándar y de error al archivo de registro
    sys.stdout = open(log_file_path, 'a')
    sys.stderr = open(log_file_path, 'a')

def print_copyright():
    copyright_text = """
PyZKTecoClocks: GUI for managing ZKTeco clocks. 
Copyright (C) 2024 Paulo Sebastian Spaciuk (Darukio)

This software is licensed under the GNU General Public License v3.0 or later.
It comes without warranty. See <https://www.gnu.org/licenses/> for details."""
    print(copyright_text)
    logging.info(copyright_text)

if __name__ == '__main__':
    main()