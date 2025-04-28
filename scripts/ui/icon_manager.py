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

import socket
from scripts.business_logic.service_manager import ServiceManager
from scripts.common.utils.errors import BaseError
import sys
import win32serviceutil
import logging
import os
import time
import win32service
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
        """
        Initializes the IconManager with the specified host, port, and parent.

        Args:
            host (str): The hostname or IP address to connect to. Defaults to 'localhost'.
            port (int): The port number to connect to. Defaults to 5000.
            parent (QObject, optional): The parent object for this instance. Defaults to None.
        """
        super().__init__(parent)
        self.host = host
        self.port = port

    def run(self):
        """
        Starts a socket server that listens for incoming connections and processes received messages.

        The method initializes a TCP socket server using the specified host and port. It listens for 
        incoming client connections in a loop. When a client connects, it receives data, decodes it 
        as a UTF-8 string, and emits the received message using the `message_received` signal. 
        After processing the message, the client connection is closed.

        Logging is used to provide debug information about the server's status and any errors that occur.

        Raises:
            Exception: Logs any exceptions that occur during the server's execution.

        Attributes:
            host (str): The hostname or IP address the server binds to.
            port (int): The port number the server listens on.
        """
        logging.debug("El servidor de sockets esta intentando iniciar")
        #logging.debug("SOCKET "+str(os.getpid()))
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #logging.debug("SERVER: "+str(server))
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

    def __init__(self):
        """
        Initializes the IconManager class.
        This constructor performs the following tasks:
        - Checks if the application is running with administrator privileges. If not, it displays an error message and exits.
        - Initializes the base class.
        - Sets up the initial state of the application, including flags for automatic startup and attendance clearing.
        - Verifies if another instance of the application is already running and exits if a duplicate instance is detected.
        - Starts a socket listener in a separate thread to handle incoming messages.
        - Manages the installation and verification of the required service.
        - Initializes the system tray icon and user interface.
        - Optionally starts the application's execution based on predefined conditions.
        Raises:
            Exception: If an error occurs during initialization, it logs the error message.
        """
        try:
            #logging.debug("PREADMIN "+str(os.getpid()) + str(is_user_admin()))
            if not is_user_admin():
                QMessageBox.critical(None, "Error", "El programa necesita permisos de administrador para ejecutarse")
                sys.exit(0)
                #run_as_admin()
                
            super().__init__()
            self.is_running = False  # Variable to indicate if the application is running
            self.checked_automatic_init = is_startup_entry_exists("Servicio Reloj de Asistencias")
            self.checked_clear_attendance = eval(config['Device_config']['clear_attendance_service'])  # State of the clear attendance checkbox

            #logging.debug("POSTADMIN "+str(os.getpid()) + str(is_user_admin()))

            if verify_duplicated_instance(sys.argv[0]):
                exit_duplicated_instance()

            # Start the socket listener in a new thread.
            self.socket_listener_thread = SocketListenerThread(parent=self)
            self.socket_listener_thread.message_received.connect(self.handle_message_received)
            self.socket_listener_thread.start()

            self.service_manager = ServiceManager()
            self.service_manager.check_and_install_service()

            self.tray_icon = None  # Variable to store the QSystemTrayIcon
            self.__init_ui()  # Initialize the user interface

            self.__opt_start_execution()
        except Exception as e:
            logging.error(f"Error al iniciar la aplicacion: {e}")

    def handle_message_received(self, message):
        """
        Handles the received message and updates the tray icon's color accordingly.

        Args:
            message (str): The message received, which determines the color to set for the tray icon.
        """
        self.set_icon_color(self.tray_icon, message)

    def __init_ui(self):
        """
        Initializes the user interface components for the application.

        This method sets up the system tray icon with an initial color and 
        calls the necessary function to create and configure the tray icon.
        """
        # Create and configure the system tray icon
        self.color_icon = "red"  # Initial icon color
        self.__create_tray_icon()  # Create the system tray icon        

    def __create_tray_icon(self):
        """
        Creates and configures the system tray icon for the application.
        This method initializes a QSystemTrayIcon with a specified icon and associates it with the main window.
        It also sets up a custom context menu with various actions for controlling the application's behavior.
        The context menu includes the following actions:
        - Start service
        - Stop service
        - Restart service
        - Reinstall service
        - Uninstall service
        - Toggle "Eliminar marcaciones" (clear attendance) checkbox
        - Toggle "Iniciar automáticamente" (automatic start) checkbox
        - Exit the application
        Additionally, the tray icon displays a tooltip and a notification message upon creation.
        Exceptions:
            Logs an error message if an exception occurs during the creation of the tray icon.
        Attributes:
            tray_icon (QSystemTrayIcon): The system tray icon instance.
        """
        file_path = os.path.join(find_marker_directory("resources"), "resources", "system_tray", f"circle-{self.color_icon}.png")  # Icon file path
        #logging.debug(file_path)

        try:
            self.tray_icon = QSystemTrayIcon(QIcon(file_path), self)  # Create QSystemTrayIcon with the icon and associated main window
            self.tray_icon.showMessage("Notificación", 'Iniciando la aplicación', QSystemTrayIcon.Information)
            self.tray_icon.setToolTip("Servicio Reloj de Asistencias")  # Tooltip text

            # Create a custom context menu
            menu = QMenu()
            action_init = self.__create_action("Iniciar servicio", lambda: self.__opt_start_execution())
            action_init.setObjectName("actionInit")
            menu.addAction(action_init)  # Action to start execution
            action_stop = self.__create_action("Detener servicio", lambda: self.__opt_stop_execution())
            action_stop.setObjectName("actionStop")
            menu.addAction(action_stop)  # Action to stop execution
            action_restart = self.__create_action("Reiniciar servicio", lambda: self.__opt_restart_execution())
            action_restart.setObjectName("actionRestart")
            menu.addAction(action_restart)  # Action to restart execution
            action_reinstall_service = self.__create_action("Reinstalar servicio", lambda: self.__opt_reinstall_service())
            action_reinstall_service.setObjectName("actionReinstallService")
            menu.addAction(action_reinstall_service)  # Action to reinstall the service
            action_uninstall_service = self.__create_action("Desinstalar servicio", lambda: self.__opt_uninstall_service())
            action_uninstall_service.setObjectName("actionUninstallService")
            menu.addAction(action_uninstall_service)  # Action to uninstall the service
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
            logging.error(f"Error al crear el icono en la bandeja del sistema: {e}")

        self.tray_icon.show()  # Show the system tray icon

    @pyqtSlot()
    def __opt_uninstall_service(self):
        """
        Uninstalls the service managed by the application.

        This method stops the service execution, removes the service from the system,
        and updates the application's state and tray icon to reflect the uninstallation.
        If the service is successfully uninstalled, a notification is displayed to the user.

        Raises:
            Exception: If an error occurs during the uninstallation process, it is logged.

        Side Effects:
            - Stops the service execution.
            - Removes the service from the system.
            - Updates the tray icon color to grey.
            - Displays a notification to the user.
            - Updates the application's running state.

        """
        try:
            self.__opt_stop_execution()
            win32serviceutil.RemoveService(self.service_manager.svc_name)
            time.sleep(5)
            if not self.check_service_running(self.service_manager.svc_name):
                self.tray_icon.showMessage("Notificación", 'El servicio se desinstaló correctamente', QSystemTrayIcon.Information)
                self.set_icon_color(self.tray_icon, "grey")  # Set the icon color to red
                self.__update_running_service(False)  # Mark that the application is not running
        except Exception as e:
            logging.error(f"Error al desinstalar el servicio: {e}")

    @pyqtSlot()
    def __opt_reinstall_service(self):
        """
        Reinstalls the service managed by the application.
        This method attempts to stop the currently running service, remove it, and then reinstall it.
        It performs multiple retries to ensure the service is properly installed and running.
        Steps:
        1. Stops the execution of the service.
        2. Removes the service using `win32serviceutil.RemoveService`.
        3. Attempts to reinstall the service with retries.
        4. Starts the service and verifies if it is running.
        5. Displays a notification if the service is successfully reinstalled.
        Retries are performed if the service fails to start, with a delay between attempts.
        Exceptions:
            - Logs errors if the service cannot be removed, installed, or started.
            - Handles specific `win32service.error` exceptions, such as service not found (error 1060).
        Attributes:
            MAX_RETRIES (int): The maximum number of retries for reinstalling the service.
        Raises:
            Logs any unexpected exceptions encountered during the process.
        """
        try:
            self.__opt_stop_execution()
            win32serviceutil.RemoveService(self.service_manager.svc_name)
            time.sleep(5)
        except Exception as e:
            logging.error(f"Error al remover el servicio: {e}")

        try:
            retries = 0
            success = False
            while retries < self.MAX_RETRIES and not success:
                try:
                    logging.info(f"Intentando instalar el servicio... Intento {retries + 1}/{self.MAX_RETRIES}")
                    #logging.debug(find_root_directory())
                    
                    self.service_manager.check_and_install_service()
                    self.__opt_start_execution()
                    if self.check_service_running(self.service_manager.svc_name):
                        self.tray_icon.showMessage("Notificación", 'El servicio se reinstaló correctamente', QSystemTrayIcon.Information)
                        success = True
                        break
                    time.sleep(1)  # Wait a moment for the service to change state
                except win32service.error as e:
                    if e.winerror == 1060:
                        logging.error(f'Error al iniciar el servicio {self.service_manager.svc_name}: {e.strerror}')
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
        Toggles the state of the "clear attendance" checkbox and updates the configuration file accordingly.

        This method inverts the current state of the `checked_clear_attendance` attribute, updates the 
        `clear_attendance_service` field in the configuration file, and writes the changes back to the file.

        If an error occurs while writing to the configuration file, it raises a `BaseError` with an error code 
        and the exception message.

        Raises:
            BaseError: If there is an issue writing to the configuration file.
        """
        self.checked_clear_attendance = not self.checked_clear_attendance  # Invert the current checkbox state
        #logging.debug(f"Status checkbox: {self.checked_clear_attendance}")  # Debug log: current checkbox state
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
        Creates a QAction with the specified text and associates it with a function.

        Args:
            text (str): The display text for the QAction.
            function (callable): The function to be executed when the action is triggered.

        Returns:
            QAction: The created QAction object with the specified text and connected function.
        """
        action = QAction(text, self)  # Create QAction with the text and associated main window
        action.triggered.connect(function)  # Connect the action to the provided function
        return action  # Return the created action
    
    def set_icon_color(self, icon: QSystemTrayIcon, color):
        """
        Updates the color of the system tray icon.

        Args:
            icon (QSystemTrayIcon): The system tray icon object to update.
            color (str): The color identifier for the icon (e.g., "red", "green", "blue").
        
        Behavior:
            - Updates the `color_icon` attribute with the specified color.
            - Constructs the file path for the icon image based on the specified color.
            - Sets the system tray icon to the new icon with the specified color.
        """
        self.color_icon = color  # Update the icon color
        file_path = os.path.join(find_marker_directory("resources"), "resources", "system_tray", f"circle-{self.color_icon}.png")  # Icon file path with the new color
        icon.setIcon(QIcon(file_path))  # Set the new icon with the specified color

    def start_timer(self):
        """
        Starts a timer by returning the current time in seconds.

        Returns:
            float: The current time in seconds since the epoch.
        """
        return time.time()  # Return the current time in seconds

    def stop_timer(self, start_time):
        """
        Stops the timer and calculates the elapsed time since the provided start time.

        Args:
            start_time (float): The starting time in seconds since the epoch.

        Returns:
            None

        Logs:
            Logs the elapsed time in seconds with a debug message.

        Notifications:
            Displays a system tray notification with the elapsed time in seconds.
        """
        end_time = self.start_timer()  # Get the end time
        elapsed_time = end_time - start_time  # Calculate the elapsed time
        logging.debug(f'The task finished in {elapsed_time:.2f} seconds')
        self.tray_icon.showMessage("Notificación", f'The task finished in {elapsed_time:.2f} seconds', QSystemTrayIcon.Information)  # Show notification with the elapsed time

    @pyqtSlot()
    def __opt_start_execution(self):
        """
        Attempts to start a service with retries and updates the system tray icon accordingly.
        This method tries to start a specified service using the service manager. It performs
        multiple retries if the service fails to start initially. The system tray icon is updated
        to reflect the service's status.
        Raises:
            Exception: If an unexpected error occurs during the service start process.
        Side Effects:
            - Displays notifications via the system tray icon.
            - Logs information, warnings, and errors related to the service start process.
            - Updates the system tray icon color based on the service status.
        Workflow:
            1. Displays a notification indicating the service is starting.
            2. Attempts to start the service up to `MAX_RETRIES` times.
            3. Logs the progress and any errors encountered during the process.
            4. Updates the system tray icon to green if the service starts successfully.
            5. Logs a critical error if the service fails to start after all retries.
        Notes:
            - The method uses `win32serviceutil.StartService` to start the service.
            - If the service is already running, it logs success and skips further attempts.
            - A delay is introduced between retries to allow the service to stabilize.
        """
        try:
            self.tray_icon.showMessage("Notificación", 'Iniciando el servicio', QSystemTrayIcon.Information)
            retries = 0
            success = False

            while retries < self.MAX_RETRIES and not success:
                try:
                    if self.check_service_running(self.service_manager.svc_name):
                        logging.info("El servicio se inicio correctamente")
                        success = True
                        break

                    logging.info(f"Intentando iniciar el servicio... Intento {retries + 1}/{self.MAX_RETRIES}")
                    #logging.debug(find_root_directory())
                    win32serviceutil.StartService(self.service_manager.svc_name, find_marker_directory(self.service_manager.svc_name))
                    time.sleep(1)  # Wait a moment for the service to change state
                except win32service.error as e:
                    if e.winerror == 1060:
                        logging.error(f'Error al iniciar el servicio {self.service_manager.svc_name}: {e.strerror}')
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
        except Exception as e:
            logging.error(e)

    def __update_running_service(self, is_running):
        """
        Updates the running status of the service.

        Args:
            is_running (bool): A flag indicating whether the service is running.
        """
        self.is_running = is_running

    def __show_message_information(self, title, text):
        """
        Displays an informational message box with a specified title and text.
        This method creates a QMessageBox with an information icon, sets its title 
        and message text, and displays it to the user. Additionally, it sets a custom 
        window icon for the message box using a fingerprint icon located in the 
        "resources" directory. After the message box is closed, it ensures that the 
        context menu of the tray icon (if available) is made visible again.
        Args:
            title (str): The title of the message box.
            text (str): The informational text to display in the message box.
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
        Stops the execution of a running service.

        This method updates the running service status to False, checks if the service is running,
        and attempts to stop it. It provides notifications through the system tray icon and logs
        the process of stopping the service. If the service stops successfully, it updates the
        tray icon color to red if it is not already yellow.

        Steps:
        1. Update the running service status to False.
        2. Check if the service is running.
        3. If the service is running, stop it and notify the user.
        4. Wait until the service is fully stopped, logging the progress.
        5. Notify the user once the service has stopped successfully.
        6. Change the tray icon color to red if it is not yellow.

        Note:
            This method interacts with Windows services and requires the `win32serviceutil` module.
            It also uses a system tray icon for notifications.

        Raises:
            Any exceptions raised by `win32serviceutil.StopService` or other service-related operations
            are not explicitly handled in this method.
        """
        self.__update_running_service(False)
        if self.check_service_running(self.service_manager.svc_name):
            win32serviceutil.StopService(self.service_manager.svc_name)
            self.tray_icon.showMessage("Notificación", 'Deteniendo el servicio', QSystemTrayIcon.Information)
            logging.debug("Deteniendo el servicio")
            while not self.check_service_stopped(self.service_manager.svc_name):
                time.sleep(1)
                logging.debug("Esperando a que el servicio se detenga...")
                if self.check_service_stopped(self.service_manager.svc_name):
                    logging.debug("Se detuvo el servicio")
                    self.tray_icon.showMessage("Notificación", 'El servicio se detuvo correctamente', QSystemTrayIcon.Information)
        if self.color_icon != "yellow":
            self.set_icon_color(self.tray_icon, "red")  # Set the icon color to red

    def check_service_stopped(self, service_name):
        """
        Checks if a Windows service is stopped.

        Args:
            service_name (str): The name of the Windows service to check.

        Returns:
            bool: True if the service is stopped, False otherwise.

        Notes:
            - This function uses the `win32serviceutil.QueryServiceStatus` method to query the status of the service.
            - A service status of 1 indicates that the service is stopped.
            - If an exception occurs during the query, the function will print an error message and return False.
        """
        try:
            status = win32serviceutil.QueryServiceStatus(service_name)
            #logging.debug(f"Estado del servicio {service_name}: {status[1]}")  # Debug log: service status
            # State 4 means it is running
            if status[1] == 1:
                return True
            return False
        except Exception as e:
            print(f"Error al verificar el estado del servicio: {e}")
            return False
        
    def check_service_running(self, service_name):
        """
        Checks if a specified Windows service is currently running.

        Args:
            service_name (str): The name of the Windows service to check.

        Returns:
            bool: True if the service is running (state 4), False otherwise or if an error occurs.

        Raises:
            Exception: If an error occurs while querying the service status, it is caught and logged.
        """
        try:
            status = win32serviceutil.QueryServiceStatus(service_name)
            #logging.debug(f"Estado del servicio {service_name}: {status[1]}")  # Debug log: service status
            #logging.debug(status[1] == 4)
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
        Restarts the execution process by stopping the current execution and starting it again.

        This method ensures that the execution process is reset by first invoking the 
        `__opt_stop_execution` method to halt any ongoing execution, followed by calling 
        the `__opt_start_execution` method to initiate a fresh execution.
        """
        self.__opt_stop_execution()  # Stop the current execution
        self.__opt_start_execution()  # Start the execution again

    @pyqtSlot()
    def __opt_toggle_checkbox_automatic_init(self):
        """
        Toggles the state of the "automatic initialization" checkbox and updates the system's startup configuration
        accordingly. If the application is running in a frozen state (e.g., packaged with PyInstaller), this method
        inverts the current checkbox state and either adds or removes the application from the system's startup
        programs.
        Actions:
            - If the checkbox is checked, the application is added to the system's startup programs.
            - If the checkbox is unchecked, the application is removed from the system's startup programs.
        Dependencies:
            - The `add_to_startup` function is used to add the application to the system's startup.
            - The `remove_from_startup` function is used to remove the application from the system's startup.
        Note:
            This method only functions when the application is running in a frozen state (e.g., as a standalone
            executable).
        Attributes:
            checked_automatic_init (bool): The current state of the "automatic initialization" checkbox.
        """
        import sys
        if getattr(sys, 'frozen', False):
            self.checked_automatic_init = not self.checked_automatic_init  # Invert the current checkbox state
            #logging.debug(f"Status checkbox: {self.checked_automatic_init}")  # Debug log: current checkbox state

            if self.checked_automatic_init:
                #logging.debug('add_to_startup')
                add_to_startup("Servicio Reloj de Asistencias")
            else:
                #logging.debug('remove_from_startup')
                remove_from_startup("Servicio Reloj de Asistencias")

    @pyqtSlot()
    def __opt_exit_icon(self):
        """
        Handles the exit operation for the application.

        This method hides the system tray icon, if it exists, and then
        gracefully exits the application by calling `QApplication.quit()`.

        Returns:
            None
        """
        if self.tray_icon:
            self.tray_icon.hide()  # Hide the system tray icon
            QApplication.quit()  # Exit the application