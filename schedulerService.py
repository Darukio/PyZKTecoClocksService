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
from datetime import datetime
import socket
import sys
import os
import time
import schedule
import win32serviceutil
import win32service
import win32event
import logging
import servicemanager
import locale

from scripts.business_logic.service_manager import AttendancesManager, HourManager
from scripts.common.utils.file_manager import file_exists_in_folder, find_root_directory, load_from_file
from version import SERVICE_VERSION

svc_python_class = "schedulerService.SchedulerService"
svc_name = "GESTOR_RELOJ_ASISTENCIA"
svc_display_name = "GESTOR RELOJ DE ASISTENCIAS"
svc_description = "Servicio para sincronización de tiempo y recuperación de datos de asistencia."

locale.setlocale(locale.LC_TIME, "Spanish_Argentina.1252")  # Español de Argentina

class SchedulerService(win32serviceutil.ServiceFramework):
    _svc_name_ = svc_name
    _svc_display_name_ = svc_display_name
    _svc_description_ = svc_description
    is_running = True
    path = find_root_directory()
    current_log_month = datetime.today().strftime("%Y-%b")

    def __init__(self, args):
        """
        Initializes the scheduler service.
        Args:
            args (list): A list of arguments passed to the service. The first argument is mandatory, 
                         and additional arguments can be used to specify a custom path.
        Attributes:
            path (str): A custom path provided as an additional argument, if any.
            hWaitStop (handle): A handle to the event object used to signal service stop.
        Raises:
            Exception: Logs any exception that occurs during initialization.
        This method performs the following:
            - Initializes the base ServiceFramework class.
            - Creates a logs folder in the root directory if it does not exist.
            - Creates a subfolder for the current log month within the logs folder.
            - Configures logging for debug and error logs using the specified log files.
            - Sets up a handle for the service stop event.
        """
        try:
            win32serviceutil.ServiceFramework.__init__(self, args)

            logs_folder = os.path.join(find_root_directory(), 'logs')

            if not os.path.exists(logs_folder):
                os.makedirs(logs_folder)

            logs_month_folder = os.path.join(logs_folder, self.current_log_month)

            if not os.path.exists(logs_month_folder):
                os.makedirs(logs_month_folder)

            debug_log_file = os.path.join(logs_month_folder, 'servicio_reloj_de_asistencias_'+SERVICE_VERSION+'_debug.log')
            error_log_file = os.path.join(logs_month_folder, 'servicio_reloj_de_asistencias_'+SERVICE_VERSION+'_error.log')

            self.configure_logging(debug_log_file, error_log_file)

            if len(args) > 1:  # Check if an extra argument was provided
                self.path = "".join(args[1:])
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        except Exception as e:
            logging.error(e)

    def SvcStop(self):
        """
        Stops the service by setting the running flag to False, reporting the service
        status as stopping, and signaling the stop event. Additionally, logs the service
        stop event for informational purposes.

        This method is typically called by the service control manager to stop the service.
        """
        self.is_running = False
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STOPPED, (self._svc_name_, ''))
        
    def SvcDoRun(self):
        """
        Executes the main logic of the service when it is started.

        This method is called when the service is run. It logs the service start event
        and then calls the `main` method to perform the primary operations of the service.
        If an exception occurs during execution, it is logged as an error.

        Raises:
            Exception: Logs any exception that occurs during the execution of the service.
        """
        try:
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ''))
            self.main()
        except Exception as e:
            logging.error(e)

    def main(self):
        """
        Main method to manage the scheduling service.
        This method configures the schedule, monitors and executes scheduled jobs,
        and handles logging reconfiguration. It also updates the status icon based
        on job execution status.
        Workflow:
        1. Configures the schedule using `self.configure_schedule()`.
        2. Continuously runs while `self.is_running` is True:
            - Reconfigures logging if needed (e.g., on month change).
            - Checks and executes pending scheduled jobs.
            - Updates the status icon to indicate job execution status.
            - Sleeps for 60 seconds between iterations.
        Exception Handling:
        - Logs any errors encountered during schedule configuration, logging
          reconfiguration, job execution, or icon updates.
        Attributes:
        - `self.is_running` (bool): Controls the execution loop.
        - `schedule.get_jobs()` (list): Retrieves the list of scheduled jobs.
        - `self.send_icon_update(status: str)`: Updates the status icon with the
          given color ('yellow' for running, 'green' for idle).
        Raises:
        - Logs unexpected exceptions during execution.
        """
        #logging.debug("Path: "+os.path.abspath(__file__))
        
        try:
            self.configure_schedule()
        except Exception as e:
            logging.error(e)

        logging.debug(f'Tareas programadas: {str(len(schedule.get_jobs()))}\n{str(schedule.get_jobs())}')
        
        while self.is_running:
            try:
                self.reconfigure_logging_if_needed()  # Check for month change.
            except Exception as e:
                logging.error(f'Error al reconfigurar los logs: {e}')

            try:
                logging.debug('Ejecutando servicio...')
                job_running = False

                for job in schedule.get_jobs():
                    #logging.debug(f'Proxima ejecucion: {job.next_run} - Hora actual: {datetime.now()} - Diferencia: {job.next_run - datetime.now()}')
                    if job.next_run <= datetime.now():
                        logging.debug(f'Ejecutando tarea...')
                        self.send_icon_update('yellow')
                        job_running = True
                        # Break after the first detection to avoid repeated calls in the same loop iteration
                        break
                schedule.run_pending()
                time.sleep(60)
            except Exception as e:
                logging.error('Error inesperado: %s %s', e, e.__cause__)

            try:
                if job_running:
                    self.send_icon_update('green')
            except Exception as e:
                logging.error(f'Error al enviar actualizacion de icono: {e}')
            finally:
                job_running = False

    def reconfigure_logging_if_needed(self):
        """
        Reconfigures the logging system if the current month has changed.

        This method checks if the current month is different from the last recorded
        logging month. If so, it creates a new directory for the logs of the new month,
        generates new log file paths for debug and error logs, and reconfigures the
        logging system to use these new files.

        The log files are named using the current service version and are stored in
        a "logs" subdirectory under the specified path.

        Side Effects:
            - Creates a new directory for the current month's logs if it doesn't exist.
            - Updates the logging configuration to use new log files.
            - Updates the `current_log_month` attribute to the new month.

        Attributes:
            self.path (str): The base path where the logs directory is located.
            self.current_log_month (str): The month of the currently active log files.
            SERVICE_VERSION (str): The version of the service, used in log file names.

        Raises:
            OSError: If the directory creation fails.
        """
        new_month = datetime.today().strftime("%Y-%b")
        if new_month != self.current_log_month:
            month_folder = os.path.join(self.path, 'logs', new_month)
            os.makedirs(month_folder, exist_ok=True)
            debug_file = os.path.join(month_folder, f'servicio_reloj_de_asistencias_{SERVICE_VERSION}_debug.log')
            error_file = os.path.join(month_folder, f'servicio_reloj_de_asistencias_{SERVICE_VERSION}_error.log')
            self.configure_logging(debug_file, error_file)
            self.current_log_month = new_month

    def configure_schedule(self):
        """
        Configures scheduled tasks based on execution times loaded from a schedule file.
        This method reads a schedule file to determine the times at which specific tasks 
        should be executed. It supports two types of tasks:
        - Managing device attendances.
        - Updating device times.
        The schedule file should contain lines specifying the execution times for each task, 
        grouped under comments that indicate the task type. For example:
            # gestionar_marcaciones_dispositivos
            08:00
            14:00
            # actualizar_hora_dispositivos
            12:00
            18:00
        Tasks are scheduled using the `schedule` library to run daily at the specified times.
        Raises:
            Exception: If there is an error loading the schedule file.
        Notes:
            - The schedule file must be named 'schedule.txt' and located in the root directory.
            - Lines starting with '#' are treated as task type indicators.
            - Non-comment lines are treated as execution times in HH:MM format.
        """
        file_path = os.path.join(self.path, 'schedule.txt')
        #logging.debug(not file_exists_in_folder('schedule.txt', file_path))
        if file_exists_in_folder('schedule.txt', file_path):
            # Path to the text file containing execution times
            file_path = os.path.join(find_root_directory(), 'schedule.txt')
        #logging.debug(file_path)

        try:
            content = load_from_file(file_path)  # Load content from the file
        except Exception as e:
            logging.error(e)  # Log error if the operation fails
            return

        manage_hours = []
        update_hours = []
        current_task = None

        for line in content:
            if line.startswith("#"):
                if "gestionar_marcaciones_dispositivos" in line:
                    current_task = "manage"
                elif "actualizar_hora_dispositivos" in line:
                    current_task = "update"
            elif line:
                if current_task == "manage":
                    manage_hours.append(line)
                elif current_task == "update":
                    update_hours.append(line)

        attendances_manager = AttendancesManager()
        if manage_hours:
            # Iterate over execution times for manage_devices_attendances
            for hour_to_perform in manage_hours:
                schedule.every().day.at(hour_to_perform).do(
                    lambda: self.safe_execute(attendances_manager.manage_devices_attendances)
                )

        hour_manager = HourManager()
        if update_hours:
            # Iterate over execution times for update_device_time
            for hour_to_perform in update_hours:
                schedule.every().day.at(hour_to_perform).do(
                    lambda: self.safe_execute(hour_manager.manage_hour_devices)
                )
    
    def send_icon_update(self, color: str, host='localhost', port=5000):
        """
        Sends an icon update message to a specified host and port using a TCP socket.

        Args:
            color (str): The color to be sent as an update. It is encoded as a UTF-8 string.
            host (str, optional): The hostname or IP address of the server to connect to. Defaults to 'localhost'.
            port (int, optional): The port number of the server to connect to. Defaults to 5000.

        Logs:
            - Logs a debug message indicating the start of the icon update process.
            - Logs an error message if an exception occurs during the process.

        Raises:
            Exception: If there is an error in creating the socket, connecting to the server, 
                       or sending the data, it will be logged as an error.
        """
        logging.debug("Envio de actualizacion de icono")
        # Create a TCP client socket to send the update message.
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, port))
            client.sendall(color.encode('utf-8'))
            client.close()
        except Exception as e:
            logging.error(f"Error al enviar actualizacion: {e}")

    def configure_logging(self, debug_file, error_file):
        """
        Configures logging for the application by setting up a debug log file and an error log file.
        This method clears any existing logging handlers to avoid duplicate or stale streams,
        then configures a debug log file for detailed logging and an error log file for warnings
        and errors.
        Args:
            debug_file (str): The file path for the debug log file where detailed logs will be written.
            error_file (str): The file path for the error log file where warnings and errors will be logged.
        Behavior:
            - Removes all existing logging handlers to ensure a clean logging configuration.
            - Sets up a debug log file with DEBUG level logging and a specific format.
            - Adds a separate handler for warnings and errors, writing them to the specified error log file.
        """
        # Always clear existing handlers to avoid stale streams
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()

        # Configure basic debug log file
        logging.basicConfig(
            filename=debug_file,
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s'
        )

        # Add handler for warnings and errors
        error_handler = logging.FileHandler(error_file)
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(error_handler)

    def safe_execute(self, func, *args, **kwargs):
        """
        Executes a given function safely, catching and logging any exceptions that occur.

        Args:
            func (callable): The function to be executed.
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.

        Logs:
            Logs an error message if an exception is raised during the execution of the function.
        """
        try:
            func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error ejecutando {func.__name__}: {e}")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(SchedulerService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(SchedulerService)