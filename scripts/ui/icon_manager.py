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

from scripts.common.utils.errors import BaseError
eventlet.monkey_patch()
original_socket = eventlet.patcher.original('socket')
import sys
import win32serviceutil
import logging
import os
import time
import win32service

from schedulerService import check_and_install_service
from scripts import config
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from scripts.common.utils.add_to_startup import add_to_startup, is_startup_entry_exists, remove_from_startup
from PyQt5.QtWidgets import QMainWindow, QSystemTrayIcon, QMenu, QAction, QMessageBox
from PyQt5.QtCore import pyqtSlot

from scripts.common.utils.file_manager import find_marker_directory, find_root_directory
from scripts.common.utils.system_utils import exit_duplicated_instance, is_user_admin, run_as_admin, verify_duplicated_instance

from PyQt5.QtCore import QThread, pyqtSignal

config.read(os.path.join(find_root_directory(), 'config.ini'))  # Read the config.ini configuration file

# This class runs in a separate thread to listen for messages from the service.
class SocketListenerThread(QThread):
    message_received = pyqtSignal(str)

    def __init__(self, host='localhost', port=5000, parent=None):
        super().__init__(parent)
        self.host = host
        self.port = port

    def run(self):
        logging.debug("Hola! El servidor de sockets está intentando iniciar")
        try:
            server = original_socket.socket(original_socket.AF_INET, original_socket.SOCK_STREAM)
            logging.debug("SERVER: "+str(server))
            server.bind((self.host, self.port))
            server.listen(5)
            while True:
                logging.debug("Corriendo servidor de sockets...")
                client, addr = server.accept()
                data = client.recv(1024)
                if data:
                    message = data.decode('utf-8').strip()
                    logging.debug(f"Mensaje recibido: {message}")
                    self.message_received.emit(message)
                client.close()
        except Exception as e:
            logging.error(f"Error en el servidor de sockets: {e}")

class MainWindow(QMainWindow):
    MAX_RETRIES = 30  # Maximum number of retries to start the service
    service_name = "GESTOR_RELOJ_ASISTENCIA"  # Service name

    def __init__(self):
        try:
            super().__init__()
            self.is_running = False  # Variable to indicate if the application is running
            self.checked_automatic_init = is_startup_entry_exists("Servicio Reloj de Asistencias")

            if not is_user_admin():
                run_as_admin()

            if verify_duplicated_instance(sys.argv[0]):
                exit_duplicated_instance()

            check_and_install_service()

            self.tray_icon = None  # Variable to store the QSystemTrayIcon
            self.__init_ui()  # Initialize the user interface

            # Start the socket listener in a new thread.
            self.socket_listener_thread = SocketListenerThread(parent=self)
            self.socket_listener_thread.message_received.connect(self.handle_message_received)
            self.socket_listener_thread.start()

            self.__opt_start_execution()
        except Exception as e:
            logging.error(f"Error al iniciar la aplicación: {e}")

    def handle_message_received(self, message):
        self.set_icon_color(self.tray_icon, message)

    def __init_ui(self):
        # Create and configure the system tray icon
        self.color_icon = "red"  # Initial icon color
        self.__create_tray_icon()  # Create the system tray icon        

    def __create_tray_icon(self):
        '''
        Create a system tray icon with a custom context menu
        '''
        file_path = os.path.join(find_marker_directory("resources"), "resources", "system_tray", f"circle-{self.color_icon}.png")  # Icon file path
        logging.debug(file_path)

        try:
            self.tray_icon = QSystemTrayIcon(QIcon(file_path), self)  # Create QSystemTrayIcon with the icon and associated main window
            self.tray_icon.showMessage("Notificación", 'Iniciando la aplicación', QSystemTrayIcon.Information)
            self.tray_icon.setToolTip("Servicio Reloj de Asistencias")  # Tooltip text

            # Create a custom context menu
            menu = QMenu()
            menu.addAction(self.__create_action("Iniciar servicio", lambda: self.__opt_start_execution()))  # Action to start execution
            menu.addAction(self.__create_action("Detener servicio", lambda: self.__opt_stop_execution()))  # Action to stop execution
            menu.addAction(self.__create_action("Reiniciar servicio", lambda: self.__opt_restart_execution()))  # Action to restart execution
            menu.addAction(self.__create_action("Reinstalar servicio", lambda: self.__opt_reinstall_service()))  # Action to reinstall the service
            menu.addSeparator()  # Context menu separator
            # Checkbox as QAction with checkable state
            clear_attendance_action = QAction("Eliminar marcaciones", menu)
            clear_attendance_action.setCheckable(True)  # Make the QAction checkable
            clear_attendance_action.setChecked(self.checked_clear_attendance)  # Set initial checkbox state
            clear_attendance_action.triggered.connect(self.__opt_toggle_checkbox_clear_attendance)  # Connect action to toggle checkbox state
            menu.addAction(clear_attendance_action)  # Add action to the menu
            # Action to toggle the checkbox state
            automatic_init_action = QAction('Iniciar automáticamente', menu)
            automatic_init_action.setCheckable(True)
            automatic_init_action.setChecked(self.checked_automatic_init)
            automatic_init_action.triggered.connect(self.__opt_toggle_checkbox_automatic_init)
            menu.addAction(automatic_init_action)
            menu.addSeparator()  # Context menu separator
            menu.addAction(self.__create_action("Salir", lambda: self.__opt_exit_icon()))  # Action to exit the application
            self.tray_icon.setContextMenu(menu)  # Assign context menu to the icon

        except Exception as e:
            logging.error(f"Error al crear el ícono en la bandeja del sistema: {e}")

        self.tray_icon.show()  # Show the system tray icon

    @pyqtSlot()
    def __opt_reinstall_service(self):
        try:
            self.__opt_stop_execution()
            win32serviceutil.RemoveService(self.service_name)
            time.sleep(5)
            retries = 0
            success = False

            while retries < self.MAX_RETRIES and not success:
                try:
                    logging.info(f"Intentando instalar el servicio... Intento {retries + 1}/{self.MAX_RETRIES}")
                    logging.debug(find_root_directory())
                    
                    check_and_install_service()
                    self.__opt_start_execution()
                    if self.check_service_running(self.service_name):
                        self.tray_icon.showMessage("Notificación", 'El servicio se reinstaló correctamente', QSystemTrayIcon.Information)
                        success = True
                        break
                    time.sleep(1)  # Wait a moment for the service to change state
                except win32service.error as e:
                    if e.winerror == 1060:
                        logging.error(f'Error al iniciar el servicio {self.service_name}: {e.strerror}')
                    return
                except Exception as e:
                    logging.error(f"Error al intentar iniciar el servicio: {e}")
                finally:
                    retries += 1
                    if not success:
                        time.sleep(15)  # Wait before trying again
        except Exception as e:
            logging.error(f"Error al reinstalar el servicio: {e}")

    @pyqtSlot()
    def __opt_toggle_checkbox_clear_attendance(self):
        """
        Option to toggle the state of the clear attendance checkbox.
        """
        self.checked_clear_attendance = not self.checked_clear_attendance  # Invert the current checkbox state
        logging.debug(f"Status checkbox: {self.checked_clear_attendance}")  # Debug log: current checkbox state
        # Modify the value of the desired field in the configuration file
        config['Device_config']['clear_attendance_service'] = str(self.checked_clear_attendance)
        # Write the changes back to the configuration file
        try:
            with open('config.ini', 'w') as config_file:
                config.write(config_file)
        except Exception as e:
            BaseError(3001, str(e))

    def __create_action(self, text, function):
        """
        Create an action for the context menu.
        
        Args:
            text (str): Action text.
            function (function): Function to be executed when the action is triggered.
            
        Returns:
            QAction: Created action.
        """
        action = QAction(text, self)  # Create QAction with the text and associated main window
        action.triggered.connect(function)  # Connect the action to the provided function
        return action  # Return the created action
    
    def set_icon_color(self, icon, color):
        """
        Change the color of the system tray icon.

        Args:
            icon (QSystemTrayIcon): System tray icon to modify.
            color (str): Color to set ('red', 'yellow', 'green').
        """
        self.color_icon = color  # Update the icon color
        file_path = os.path.join(find_marker_directory("resources"), "resources", "system_tray", f"circle-{self.color_icon}.png")  # Icon file path with the new color
        icon.setIcon(QIcon(file_path))  # Set the new icon with the specified color

    def start_timer(self):
        """
        Start the timer and return the current time.

        Returns:
            float: Current time in seconds.
        """
        return time.time()  # Return the current time in seconds

    def stop_timer(self, start_time):
        """
        Stop the timer, calculate the elapsed time, and show a notification.

        Args:
            start_time (float): Start time obtained when starting the timer.
        """
        end_time = self.start_timer()  # Get the end time
        elapsed_time = end_time - start_time  # Calculate the elapsed time
        logging.debug(f'The task finished in {elapsed_time:.2f} seconds')
        self.tray_icon.showMessage("Notificación", f'The task finished in {elapsed_time:.2f} seconds', QSystemTrayIcon.Information)  # Show notification with the elapsed time

    @pyqtSlot()
    def __opt_start_execution(self):
        """
        Option to start the application execution with retries and service status verification.
        """
        self.tray_icon.showMessage("Notificación", 'Iniciando el servicio', QSystemTrayIcon.Information)
        retries = 0
        success = False

        while retries < self.MAX_RETRIES and not success:
            try:
                if self.check_service_running(self.service_name):
                    logging.info("El servicio se inicio correctamente")
                    success = True
                    break

                logging.info(f"Intentando iniciar el servicio... Intento {retries + 1}/{self.MAX_RETRIES}")
                logging.debug(find_root_directory())
                win32serviceutil.StartService(self.service_name, find_root_directory())
                time.sleep(1)  # Wait a moment for the service to change state
            except win32service.error as e:
                if e.winerror == 1060:
                    logging.error(f'Error al iniciar el servicio {self.service_name}: {e.strerror}')
                return
            except Exception as e:
                logging.error(f"Error al intentar iniciar el servicio: {e}")
            finally:
                retries += 1
                if not success:
                    time.sleep(5)  # Wait before trying again

        if success:
            self.__update_running_service(True)  # Mark that the application is running
            self.set_icon_color(self.tray_icon, "green")  # Set the icon color to green
        else:
            logging.critical("No se pudo iniciar el servicio despues de multiples intentos")

    def __update_running_service(self, is_running):
        self.is_running = is_running

    def __show_message_information(self, title, text):
        """
        Show a dialog box with a message.

        Args:
            title (str): Dialog box title.
            text (str): Message text.
        """
        msg_box = QMessageBox()  # Create QMessageBox instance
        msg_box.setWindowTitle(title)  # Set the dialog box title
        msg_box.setText(text)  # Set the message text
        msg_box.setIcon(QMessageBox.Information)  # Set the dialog box icon (information)
        file_path = os.path.join(find_marker_directory("resources"), "resources", "fingerprint.ico")
        msg_box.setWindowIcon(QIcon(file_path))
        msg_box.exec_()  # Show the dialog box

        # Once the QMessageBox is closed, show the context menu again
        if self.tray_icon:
            self.tray_icon.contextMenu().setVisible(True)

    @pyqtSlot()
    def __opt_stop_execution(self):
        """
        Option to stop the application execution.
        """
        self.__update_running_service(False)
        if self.check_service_running(self.service_name):
            win32serviceutil.StopService(self.service_name)
            self.tray_icon.showMessage("Notificación", 'Deteniendo el servicio', QSystemTrayIcon.Information)
            logging.debug("Deteniendo el servicio")
            while not self.check_service_stopped(self.service_name):
                time.sleep(1)
                logging.debug("Esperando a que el servicio se detenga...")
                if self.check_service_stopped(self.service_name):
                    logging.debug("Se detuvo el servicio")
                    self.tray_icon.showMessage("Notificación", 'El servicio se detuvo correctamente', QSystemTrayIcon.Information)
        if self.color_icon != "yellow":
            self.set_icon_color(self.tray_icon, "red")  # Set the icon color to red

    def check_service_stopped(self, service_name):
        try:
            status = win32serviceutil.QueryServiceStatus(service_name)
            logging.debug(f"Estado del servicio {service_name}: {status[1]}")  # Debug log: service status
            # State 4 means it is running
            if status[1] == 1:
                return True
            return False
        except Exception as e:
            print(f"Error al verificar el estado del servicio: {e}")
            return False
        
    def check_service_running(self, service_name):
        try:
            status = win32serviceutil.QueryServiceStatus(service_name)
            logging.debug(f"Estado del servicio {service_name}: {status[1]}")  # Debug log: service status
            logging.debug(status[1] == 4)
            # State 4 means it is running
            if status[1] == 4:
                return True
            return False
        except Exception as e:
            print(f"Error al verificar el estado del servicio: {e}")
            return False

    @pyqtSlot()
    def __opt_restart_execution(self):
        """
        Option to restart the application execution.
        """
        self.__opt_stop_execution()  # Stop the current execution
        self.__opt_start_execution()  # Start the execution again

    @pyqtSlot()
    def __opt_toggle_checkbox_automatic_init(self):
        """
        Option to toggle the state of the run at startup checkbox.
        """
        import sys
        if getattr(sys, 'frozen', False):
            self.checked_automatic_init = not self.checked_automatic_init  # Invert the current checkbox state
            logging.debug(f"Status checkbox: {self.checked_automatic_init}")  # Debug log: current checkbox state

            if self.checked_automatic_init:
                logging.debug('add_to_startup')
                add_to_startup("Servicio Reloj de Asistencias")
            else:
                logging.debug('remove_from_startup')
                remove_from_startup("Servicio Reloj de Asistencias")

    @pyqtSlot()
    def __opt_exit_icon(self):
        """
        Option to exit the application.
        """
        if self.tray_icon:
            self.tray_icon.hide()  # Hide the system tray icon
            QApplication.quit()  # Exit the application