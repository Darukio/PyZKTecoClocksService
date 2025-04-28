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

import configparser
import logging
from logging import config
import os
from scripts.common.business_logic.attendances_manager import AttendancesManagerBase
from scripts.common.business_logic.connection_manager import ConnectionManager
from scripts.common.business_logic.device_manager import get_devices_info
from scripts.common.business_logic.models.attendance import Attendance
from scripts.common.business_logic.models.device import Device
from scripts.common.business_logic.hour_manager import HourManagerBase
from scripts.common.business_logic.shared_state import SharedState
from scripts.common.utils.errors import BatteryFailingError, NetworkError, ConnectionFailedError, BaseError, ObtainAttendancesError, OutdatedTimeError
from scripts.common.utils.file_manager import find_root_directory
config = configparser.ConfigParser()
import win32serviceutil
import win32service

class AttendancesManager(AttendancesManagerBase):
    def __init__(self):
        """
        Initializes the ServiceManager instance.

        This constructor sets up the shared state for the service manager
        by creating an instance of `SharedState` and passing it to the
        superclass initializer.

        Attributes:
            state (SharedState): The shared state object used to manage
            the service's state.
        """
        self.state = SharedState()
        super().__init__(self.state)

    def manage_devices_attendances(self):
        """
        Manages the attendance data for devices.
        This method reads configuration settings, resets the state, retrieves
        device information, and processes attendance data for active devices.
        Raises:
            BaseError: If there is an error while retrieving device information.
        Returns:
            The result of the parent class's `manage_devices_attendances` method,
            called with the IP addresses of active devices.
        """
        config.read(os.path.join(find_root_directory(), 'config.ini'))
        self.clear_attendance: bool = config.getboolean('Device_config', 'clear_attendance_service')
        self.state.reset()
        all_devices: list[Device] = []
        try:
            all_devices = get_devices_info()
        except Exception as e:
            raise BaseError(3001, str(e))
        
        if len(all_devices) > 0:
            selected_ips: list[str] = [device.ip for device in all_devices if device.active]
            return super().manage_devices_attendances(selected_ips)
    
    def manage_attendances_of_one_device(self, device: Device):
        """
        Manages the attendance records of a single device.
        This method handles the connection to a device, retrieves attendance records,
        processes and formats them, and updates the device's time and name if necessary.
        It also manages individual and global attendance records and handles errors
        during the process.
        Args:
            device (Device): The device object containing information such as IP address,
                             communication type, and other metadata.
        Raises:
            ConnectionFailedError: If the connection to the device fails.
            BaseError: If an unexpected error occurs during the process.
        Returns:
            None
        """
        try:
            try:
                conn_manager = ConnectionManager(device.ip, 4370, device.communication)
                #import time
                #start_time = time.time()
                conn_manager.connect_with_retry()
                #end_time = time.time()
                #logging.debug(f'{device.ip} - Tiempo de conexión total: {(end_time - start_time):2f}')
                attendances: list[Attendance] = conn_manager.get_attendances()
                #logging.info(f'{device.ip} - PREFORMATEO - Longitud marcaciones: {len(attendances)} - Marcaciones: {attendances}')
                attendances, attendances_with_error = self.format_attendances(attendances, device.id)
                if len(attendances_with_error) > 0:
                    self.clear_attendance = False
                    logging.debug(f'No se eliminaran las marcaciones correspondientes al dispositivo {device.ip}')
                #logging.info(f'{device.ip} - POSTFORMATEO - Longitud marcaciones: {len(attendances)} - Marcaciones: {attendances}')
                logging.debug(f'clear_attendance: {self.clear_attendance}')
                conn_manager.clear_attendances(self.clear_attendance)
            except (NetworkError, ObtainAttendancesError) as e:
                with self.lock:
                    self.attendances_count_devices[device.ip] = {
                        "connection failed": True
                    }
                raise ConnectionFailedError(device.model_name, device.point, device.ip)
            except Exception as e:
                raise BaseError(3000, str(e)) from e
                        
            try:
                logging.debug(find_root_directory())
                device.model_name = conn_manager.update_device_name()
            except Exception as e:
                pass

            self.manage_individual_attendances(device, attendances)
            self.manage_global_attendances(attendances)

            try:
                conn_manager.update_time()
            except NetworkError as e:
                NetworkError(f'{device.model_name}, {device.point}, {device.ip}')
            except OutdatedTimeError as e:
                HourManager().update_battery_status(device.ip)
                BatteryFailingError(device.model_name, device.point, device.ip)

            with self.lock:
                self.attendances_count_devices[device.ip] = {
                    "attendance count": str(len(attendances))
                }
        except ConnectionFailedError as e:
            pass
        except Exception as e:
            BaseError(3000, str(e), level="warning")
        finally:
            if conn_manager.is_connected():
                conn_manager.disconnect()
        return
        
class HourManager(HourManagerBase):
    def __init__(self):
        """
        Initializes the ServiceManager instance.

        This constructor sets up the initial state of the service manager by 
        creating a shared state object and passing it to the parent class 
        initializer.

        Attributes:
            state (SharedState): An instance of the SharedState class used to 
            manage shared data across the service.
        """
        self.state = SharedState()
        super().__init__(self.state)

    def manage_hour_devices(self):
        """
        Manages the synchronization of time for active devices.
        This method retrieves information about all devices, filters the active ones,
        and updates their time settings by invoking the parent class's `update_devices_time` method.
        Raises:
            BaseError: If there is an error while retrieving device information.
        Returns:
            Any: The result of the `update_devices_time` method from the parent class.
        """
        self.state.reset()
        all_devices: list[Device] = []
        try:
            all_devices = get_devices_info()
        except Exception as e:
            raise BaseError(3001, str(e))

        if len(all_devices) > 0:
            selected_ips: list[str] = [device.ip for device in all_devices if device.active]
            return super().update_devices_time(selected_ips)

    def update_device_time_of_one_device(self, device: Device):
        """
        Updates the time on a single device by establishing a connection and synchronizing its clock.

        Args:
            device (Device): The device object containing details such as IP address, communication type, 
                             and other metadata required for connection and time update.

        Raises:
            ConnectionFailedError: Raised when the connection to the device fails.
            BatteryFailingError: Raised when the device's time cannot be updated due to a battery issue.
            BaseError: Raised for any other unexpected errors, with an error code and message.

        Notes:
            - The method uses a connection manager to handle the connection to the device.
            - Device-specific errors are tracked in the `devices_errors` dictionary, which is thread-safe.
            - Ensures proper disconnection from the device in the `finally` block if connected.
        """
        try:
            try:
                conn_manager: ConnectionManager = ConnectionManager(device.ip, 4370, device.communication)
                conn_manager.connect_with_retry()
                with self.lock:
                    self.devices_errors[device.ip] = { "connection failed": False }
                conn_manager.update_time()
                with self.lock:
                    self.devices_errors[device.ip] = { "battery failing": False }
            except NetworkError as e:
                with self.lock:
                    self.devices_errors[device.ip] = { "connection failed": True }
                raise ConnectionFailedError(device.model_name, device.point, device.ip)
            except OutdatedTimeError as e:
                with self.lock:
                    self.devices_errors[device.ip] = { "battery failing": True }
                HourManager().update_battery_status(device.ip)
                raise BatteryFailingError(device.model_name, device.point, device.ip)
        except ConnectionFailedError as e:
            pass
        except BatteryFailingError as e:
            pass
        except Exception as e:
            BaseError(3000, str(e), level="warning")
        finally:
            if conn_manager.is_connected():
                conn_manager.disconnect()
        return
    
class ServiceManager:
    svc_python_class = "schedulerService.SchedulerService"
    svc_name = "GESTOR_RELOJ_ASISTENCIA"
    svc_display_name = "GESTOR RELOJ DE ASISTENCIAS"
    svc_description = "Servicio para sincronización de tiempo y recuperación de datos de asistencia."
    
    def __init__(self):
        super().__init__()

    def service_is_installed(self, service_name):
        """
        Checks if a Windows service is installed on the system.

        Args:
            service_name (str): The name of the service to check.

        Returns:
            bool: True if the service is installed, False otherwise.

        Notes:
            - This function uses the `pywin32` library to interact with the Windows
              Service Control Manager (SCM).
            - If the service cannot be opened, it is assumed to be not installed.
            - Logs a warning if the service is not installed.
            - Handles exceptions and returns False in case of errors.

        Raises:
            None: All exceptions are caught and handled within the function.
        """
        try:
            # Open the service control manager
            scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
            try:
                # Try to open the service
                service = win32service.OpenService(scm, service_name, win32service.SERVICE_QUERY_STATUS)
                # If the service can be opened, it is installed
                win32service.CloseServiceHandle(service)
                return True
            except win32service.error as e:
                # If the error is ERROR_SERVICE_DOES_NOT_EXIST, the service is not installed
                logging.warning("Servicio no instalado")
                return False
            finally:
                win32service.CloseServiceHandle(scm)
        except Exception as e:
            print(f"Error al verificar el servicio: {e}")
            return False
        
    def check_and_install_service(self):
        """
        Checks if a Windows service is installed, and installs it if it is not.
        This method verifies whether the service specified by `self.svc_name` is installed.
        If the service is not installed, it attempts to install it using the provided
        service configuration details such as the Python class string, service name,
        display name, executable name, description, and start type.
        Installation involves locating the `schedulerService.exe` executable in the root
        directory and using the `win32serviceutil.InstallService` function to register
        the service with the Windows Service Manager.
        Logs appropriate messages for success, failure, or if the service is already installed.
        Raises:
            Exception: Logs an error message if an exception occurs during the installation process.
        Returns:
            None
        """
        if not self.service_is_installed(self.svc_name):
            # Install the service if it is not installed
            try:
                #logging.debug(os.path.join(find_marker_directory("schedulerService.exe"), 'schedulerService.exe'))
                exe_name = None
                if os.path.isfile(os.path.join(find_root_directory(), 'schedulerService.exe')):
                    exe_name = os.path.join(find_root_directory(), 'schedulerService.exe')
                    #logging.debug("EXE: "+exe_name)
                win32serviceutil.InstallService(pythonClassString=self.svc_python_class, serviceName=self.svc_name, displayName=self.svc_display_name, exeName=exe_name, description=self.svc_description, startType=win32service.SERVICE_AUTO_START)
                
            except Exception as e:
                logging.error(f'Error al instalar el servicio {self.svc_name}: {e}')
                return
            logging.info(f'Servicio {self.svc_name} instalado correctamente')
        else:
            logging.info(f'Servicio {self.svc_name} ya instalado')