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
from version import SERVICE_VERSION

# To read an INI file
from scripts import config
config.read(os.path.join(find_root_directory(), 'config.ini'))

def main():
    """
    The main entry point for the application.
    This function initializes logging, sets up the application mode (User or Developer),
    and starts the main event loop for the PyQt application. It also handles any 
    exceptions that occur during the application's execution.
    Steps performed:
    1. Configures logging with a version-specific identifier.
    2. Logs the script execution status and initializes console logging.
    3. Determines the application mode based on whether the script is frozen or not.
    4. Logs and prints the service version and mode information.
    5. Displays copyright information.
    6. Initializes the PyQt application and launches the main window.
    7. Handles any exceptions by logging a critical error.
    Raises:
        Exception: If an error occurs during the application's execution, it is caught
                   and logged as a critical error with a specific error code.
    """
    config_log("icono_reloj_de_asistencias_" + SERVICE_VERSION)

    logging.debug('Script ejecutandose...')
    #logging.debug(os.getcwd())
    #logging.debug(os.path.basename(__file__))
    #logging.debug(f'ADMIN: {is_user_admin()}')

    config_log_console()
        
    MODE = 'User' if getattr(sys, 'frozen', False) else 'Developer'
    msg_init = f"Service version: {SERVICE_VERSION} - Mode: {MODE}"
    logging.info(msg_init)
    print(msg_init)
    print_copyright()

    #config_content()
    #logging.debug(sys.argv)
    
    try:
        app = QApplication(sys.argv)
        MainWindow()
        sys.exit(app.exec_())
    except Exception as e:
        BaseError(3000, str(e), "critical")

def config_content():
    """
    Logs the sections and their corresponding key-value pairs from a configuration object.

    This function iterates through all sections of a configuration object (`config`),
    logging the section names and their respective key-value pairs for debugging purposes.

    Note:
        The `config` object is expected to be an instance of `configparser.ConfigParser`
        or a similar object that provides `sections()` and `items()` methods.

    Logging:
        - Logs the name of each section.
        - Logs each key-value pair within the section.

    Raises:
        AttributeError: If `config` does not have the required methods (`sections` and `items`).
    """
    for section in config.sections():
        logging.debug(f'Seccion: {section}')
        # Iterate over the keys and values within each section
        for key, value in config.items(section):
            logging.debug(f'Sub-seccion: {key}, Valor: {value}')

def config_log_console():
    """
    Configures logging to redirect standard output and error streams to a log file.
    This function ensures that a log file named 'console_log.txt' is created in a 
    'logs' directory located at the root of the project. If the directory or file 
    does not exist, they are created. Standard output (`sys.stdout`) and standard 
    error (`sys.stderr`) are then redirected to this log file, allowing all console 
    output and errors to be logged.
    Note:
        - The root directory is determined by the `find_root_directory()` function.
        - The log file is opened in append mode to preserve existing logs.
    Raises:
        OSError: If there is an issue creating the directory or file.
    """
    log_file_path = os.path.join(find_root_directory(), 'logs', 'console_log.txt')
    #logging.debug(find_root_directory())
    #logging.debug(sys.executable)
    
    # Ensure the log file and its directory exist
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    if not os.path.exists(log_file_path):
        with open(log_file_path, 'w') as f:
            pass  # Create the file if it doesn't exist

    # Redirect standard output and error to the log file
    sys.stdout = open(log_file_path, 'a')
    sys.stderr = open(log_file_path, 'a')

def print_copyright():
    """
    Prints and logs the copyright information for the PyZKTecoClocks application.
    The copyright information includes details about the software's purpose,
    author, licensing under the GNU General Public License v3.0 or later, 
    and a disclaimer about the lack of warranty.
    """
    copyright_text = """
PyZKTecoClocks: GUI for managing ZKTeco clocks. 
Copyright (C) 2024 Paulo Sebastian Spaciuk (Darukio)

This software is licensed under the GNU General Public License v3.0 or later.
It comes without warranty. See <https://www.gnu.org/licenses/> for details."""
    print(copyright_text)
    logging.info(copyright_text)

if __name__ == '__main__':
    main()