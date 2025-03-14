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
from scripts.common.utils.errors import BaseError
from scripts.common.utils.system_utils import is_user_admin
from PyQt5.QtWidgets import QApplication
from scripts.ui.icon_manager import MainWindow
from scripts.common.utils.logging import config_log, logging
from scripts.common.utils.file_manager import find_root_directory
import sys
import os

# Program version
VERSION = "v2.0.0"

# To read an INI file
from scripts import config
config.read(os.path.join(find_root_directory(), 'config.ini'))

def main():
    config_log("icon_for_service")

    logging.debug('Script ejecutandose...')
    logging.debug(os.getcwd())
    logging.debug(f'ADMIN: {is_user_admin()}')

    config_log_console()
        
    MODE = 'User' if getattr(sys, 'frozen', False) else 'Developer'
    msg_init = f"Program version: {VERSION} - Mode: {MODE}"
    logging.info(msg_init)
    print(msg_init)
    print_copyright()

    config_content()
    logging.debug(sys.argv)
    
    try:
        app = QApplication(sys.argv)
        MainWindow()
        sys.exit(app.exec_())
    except Exception as e:
        BaseError(3000, str(e), "critical")

def config_content():
    for section in config.sections():
        logging.debug(f'Seccion: {section}')
        # Iterate over the keys and values within each section
        for key, value in config.items(section):
            logging.debug(f'Sub-seccion: {key}, Valor: {value}')

def config_log_console():
    log_file_path = os.path.join(find_root_directory(), 'logs', 'console_log.txt')
    logging.debug(find_root_directory())
    logging.debug(sys.executable)
    
    # Ensure the log file and its directory exist
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    if not os.path.exists(log_file_path):
        with open(log_file_path, 'w') as f:
            pass  # Create the file if it doesn't exist

    # Redirect standard output and error to the log file
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