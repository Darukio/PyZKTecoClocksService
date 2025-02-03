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
import win32serviceutil
import logging
import os
import time
import win32service

from schedulerService import check_and_install_service
from scripts.ui.device_attendance_count_dialog import DeviceAttendancesCountDialog
from scripts.ui.device_attendance_dialog import DeviceAttendancesDialog
from scripts.ui.logs_dialog import LogsDialog
from scripts.ui.message_box import MessageBox
from scripts.ui.modify_device_dialog import ModifyDevicesDialog
from scripts.ui.ping_devices_dialog import PingDevicesDialog
from scripts.ui.restart_devices_dialog import RestartDevicesDialog
from ..utils.add_to_startup import *
from ..utils.errors import *
from ..utils.file_manager import *
from ..business_logic.attendances_manager import *
from ..business_logic.hour_manager import *
from scripts import config
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from ..utils.add_to_startup import is_startup_entry_exists
from PyQt5.QtWidgets import QMainWindow, QSystemTrayIcon, QMenu, QAction, QMessageBox
from PyQt5.QtCore import pyqtSlot

config.read(os.path.join(find_root_directory(), 'config.ini'))  # Read the config.ini configuration file

class MainWindow(QMainWindow):
    MAX_RETRIES = 30  # Maximum number of retries to start the service
    service_name = "GESTOR_RELOJ_ASISTENCIA"  # Service name

    def __init__(self):
        super().__init__()
        self.is_running = False  # Variable to indicate if the application is running
        logging.debug(config)
        self.checked_clear_attendance = eval(config['Device_config']['clear_attendance'])  # State of the clear attendance checkbox
        self.checked_automatic_init = is_startup_entry_exists()

        self.tray_icon = None  # Variable to store the QSystemTrayIcon
        self.__init_ui()  # Initialize the user interface

        #self.__opt_start_execution()

    def __init_ui(self):
        self.setWindowTitle('Ventana principal')  # Main window title
        self.setGeometry(100, 100, 400, 300)  # Main window geometry (position and size)

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
            self.tray_icon.setToolTip("Gestor Reloj de Asistencias")  # Tooltip text

            # Create a custom context menu
            menu = QMenu()
            menu.addAction(self.__create_action("Iniciar servicio", lambda: self.__opt_start_execution()))  # Action to start execution
            menu.addAction(self.__create_action("Detener servicio", lambda: self.__opt_stop_execution()))  # Action to stop execution
            menu.addAction(self.__create_action("Reiniciar servicio", lambda: self.__opt_restart_execution()))  # Action to restart execution
            menu.addAction(self.__create_action("Reinstalar servicio", lambda: self.__opt_reinstall_service()))  # Action to reinstall the service
            menu.addSeparator()  # Context menu separator
            menu.addAction(self.__create_action("Modificar dispositivos...", lambda: self.__opt_modify_devices()))  # Action to modify devices
            menu.addAction(self.__create_action("Reiniciar dispositivos...", lambda: self.__opt_restart_devices()))  # Action to restart devices    
            menu.addAction(self.__create_action("Probar conexiones...", lambda: self.__opt_test_connections()))  # Action to test connections
            menu.addAction(self.__create_action("Actualizar hora", lambda: self.__opt_update_devices_time()))  # Action to update device time
            menu.addAction(self.__create_action("Obtener marcaciones...", lambda: self.__opt_fetch_devices_attendances()))  # Action to fetch device attendances
            menu.addAction(self.__create_action("Obtener cantidad de marcaciones...", lambda: self.__opt_show_attendances_count()))  # Action to show attendance count
            menu.addSeparator()  # Context menu separator
            # Checkbox as QAction with checkable state
            clear_attendance_action = QAction("Eliminar marcaciones", menu)
            clear_attendance_action.setCheckable(True)  # Make the QAction checkable
            clear_attendance_action.setChecked(self.checked_clear_attendance)  # Set initial checkbox state
            clear_attendance_action.triggered.connect(self.__opt_toggle_checkbox_clear_attendance)  # Connect action to toggle checkbox state
            menu.addAction(clear_attendance_action)  # Add action to the menu

            logging.debug(f'checked_automatic_init: {self.checked_automatic_init}')
            # Action to toggle the checkbox state
            automatic_init_action = QAction('Iniciar automáticamente', menu)
            automatic_init_action.setCheckable(True)
            automatic_init_action.setChecked(self.checked_automatic_init)
            automatic_init_action.triggered.connect(self.__opt_toggle_checkbox_automatic_init)
            menu.addAction(automatic_init_action)
            menu.addSeparator()  # Context menu separator
            menu.addAction(self.__create_action("Ver errores...", lambda: self.__opt_show_logs()))  # Action to show logs
            menu.addAction(self.__create_action("Salir", lambda: self.__opt_exit_icon()))  # Action to exit the application
            self.tray_icon.setContextMenu(menu)  # Assign context menu to the icon

        except Exception as e:
            logging.error(f"Error al crear el ícono en la bandeja del sistema: {e}")

        self.tray_icon.show()  # Show the system tray icon

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
    
    def __set_icon_color(self, icon, color):
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
            self.__set_icon_color(self.tray_icon, "green")  # Set the icon color to green
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
            self.__set_icon_color(self.tray_icon, "red")  # Set the icon color to red

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
    def __opt_modify_devices(self):
        """
        Option to test device connections.
        """
        self.__set_icon_color(self.tray_icon, "yellow")  # Set the icon color to yellow
        try:
            device_dialog = ModifyDevicesDialog()  # Get device status
            device_dialog.exec_()
            self.__set_icon_color(self.tray_icon, "green" if self.is_running else "red")  # Restore icon color based on execution status
            # Once the QMessageBox is closed, show the context menu again
            if self.tray_icon:
                self.tray_icon.contextMenu().setVisible(True)
        except Exception as e:
            logging.error(f"Error al modificar dispositivos: {e}")  # Log error if the operation fails

    @pyqtSlot()
    def __opt_show_logs(self):
        """
        Option to show logs.
        """
        self.__set_icon_color(self.tray_icon, "yellow")  # Set the icon color to yellow
        try:
            error_log_dialog = LogsDialog()  # Get device status
            error_log_dialog.exec_()
            self.__set_icon_color(self.tray_icon, "green" if self.is_running else "red")  # Restore icon color based on execution status
            # Once the QMessageBox is closed, show the context menu again
            if self.tray_icon:
                self.tray_icon.contextMenu().setVisible(True)
        except Exception as e:
            logging.error(f"Error al mostrar conexiones de dispositivos: {e}")  # Log error if the operation fails

    @pyqtSlot()
    def __opt_restart_devices(self):
        """
        Option to restart devices.
        """
        self.__set_icon_color(self.tray_icon, "yellow")  # Set the icon color to yellow
        try:
            restart_devices_dialog = RestartDevicesDialog()  # Get device status
            restart_devices_dialog.exec_()
            self.__set_icon_color(self.tray_icon, "green" if self.is_running else "red")  # Restore icon color based on execution status
            # Once the QMessageBox is closed, show the context menu again
            if self.tray_icon:
                self.tray_icon.contextMenu().setVisible(True)
        except Exception as e:
            logging.error(f"Error al mostrar reinicio dispositivos: {e}")  # Log error if the operation fails

    @pyqtSlot()
    def __opt_test_connections(self):
        """
        Option to test device connections.
        """
        self.__set_icon_color(self.tray_icon, "yellow")  # Set the icon color to yellow
        try:
            device_status_dialog = PingDevicesDialog()  # Get device status
            device_status_dialog.op_terminated.connect(self.stop_timer)
            device_status_dialog.exec_()
            self.__set_icon_color(self.tray_icon, "green" if self.is_running else "red")  # Restore icon color based on execution status
            # Once the QMessageBox is closed, show the context menu again
            if self.tray_icon:
                self.tray_icon.contextMenu().setVisible(True)
        except Exception as e:
            logging.error(f"Error al mostrar conexiones de dispositivos: {e}")  # Log error if the operation fails

    @pyqtSlot()
    def __opt_update_devices_time(self):
        """
        Option to update the time on devices.
        """
        self.__set_icon_color(self.tray_icon, "yellow")  # Set the icon color to yellow
        start_time = self.start_timer()  # Start the timer
        update_device_time()  # Call function to update time on devices (assumed to be defined elsewhere)
        self.stop_timer(start_time)  # Stop the timer and show notification
        self.__set_icon_color(self.tray_icon, "green" if self.is_running else "red")  # Restore icon color based on execution status

    @pyqtSlot()
    def __opt_fetch_devices_attendances(self):
        """
        Option to fetch device attendances.
        """
        self.__set_icon_color(self.tray_icon, "yellow")  # Set the icon color to yellow
        try:
            device_attendances_dialog = DeviceAttendancesDialog()
            device_attendances_dialog.op_terminated.connect(self.stop_timer)
            device_attendances_dialog.exec_()
            self.__set_icon_color(self.tray_icon, "green" if self.is_running else "red")  # Restore icon color based on execution status
            # Once the QMessageBox is closed, show the context menu again
            if self.tray_icon:
                self.tray_icon.contextMenu().setVisible(True)
        except Exception as e:
            logging.error(f"Error al obtener marcaciones: {e}")  # Log error if the operation fails

    @pyqtSlot()
    def __opt_show_attendances_count(self):
        """
        Option to show the number of attendances per device.
        """
        self.__set_icon_color(self.tray_icon, "yellow")  # Set the icon color to yellow
        try:
            device_attendances_count_dialog = DeviceAttendancesCountDialog()
            device_attendances_count_dialog.op_terminated.connect(self.stop_timer)
            device_attendances_count_dialog.exec_()
            self.__set_icon_color(self.tray_icon, "green" if self.is_running else "red")  # Restore icon color based on execution status
            # Once the QMessageBox is closed, show the context menu again
            if self.tray_icon:
                self.tray_icon.contextMenu().setVisible(True)
        except Exception as e:
            logging.error(f"Error al mostrar cantidad de marcaciones: {e}")  # Log error if the operation fails

    @pyqtSlot()
    def __opt_toggle_checkbox_clear_attendance(self):
        """
        Option to toggle the state of the clear attendance checkbox.
        """
        self.checked_clear_attendance = not self.checked_clear_attendance  # Invert the current checkbox state
        logging.debug(f"Status checkbox: {self.checked_clear_attendance}")  # Debug log: current checkbox state
        # Modify the value of the desired field in the configuration file
        config['Device_config']['clear_attendance'] = str(self.checked_clear_attendance)
        # Write the changes back to the configuration file
        with open('config.ini', 'w') as config_file:
            config.write(config_file)

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
                add_to_startup()
            else:
                logging.debug('remove_from_startup')
                remove_from_startup()

    @pyqtSlot()
    def __opt_exit_icon(self):
        """
        Option to exit the application.
        """
        if self.tray_icon:
            # if len(schedule.get_jobs()) >= 1:
            #self.__opt_stop_execution()  # Stop the execution if there are scheduled jobs
            self.tray_icon.hide()  # Hide the system tray icon
            QApplication.quit()  # Exit the application

    def thread_manage_device_attendances(self):
        self.__set_icon_color(self.tray_icon, "yellow")
        try:
            manage_device_attendances(from_service=True)
        except Exception as e:
            logging.critical(e)
        self.__set_icon_color(self.tray_icon, "green" if self.is_running else "red")  # Restore icon color based on execution status

    def thread_update_device_time(self):
        self.__set_icon_color(self.tray_icon, "yellow")
        try:
            update_device_time(from_service=True)
        except Exception as e:
            logging.critical(e)
        self.__set_icon_color(self.tray_icon, "green" if self.is_running else "red")  # Restore icon color based on execution status