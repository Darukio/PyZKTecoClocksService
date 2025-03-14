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
original_socket = eventlet.patcher.original('socket')
from datetime import datetime
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
from PyQt5.QtCore import QThread

from scripts.common.business_logic.attendances_manager import manage_device_attendances
from scripts.common.business_logic.hour_manager import update_devices_time
from scripts.common.utils.file_manager import file_exists_in_folder, find_root_directory, load_from_file

svc_python_class = "schedulerService.SchedulerService"
svc_name = "GESTOR_RELOJ_ASISTENCIA"
svc_display_name = "GESTOR RELOJ DE ASISTENCIAS"
svc_description = "Servicio para sincronización de tiempo y recuperación de datos de asistencia."

locale.setlocale(locale.LC_TIME, "Spanish_Argentina.1252")  # Español de Argentina

def configure_logging(debug_log_file, error_log_file):
    # Verificar si ya hay handlers configurados antes de llamar a basicConfig
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            filename=debug_log_file if debug_log_file else "default_debug.log",
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s'
        )

    # Verificar si el manejador de errores ya está agregado
    error_handler_exists = any(isinstance(h, logging.FileHandler) and h.baseFilename == error_log_file
                               for h in logging.getLogger().handlers)

    if not error_handler_exists:
        try:
            error_logger = logging.FileHandler(error_log_file)
            error_logger.setLevel(logging.WARNING)
            error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            error_logger.setFormatter(error_formatter)
            logging.getLogger().addHandler(error_logger)
        except Exception as e:
            logging.error(f"Error al configurar el manejador de errores: {e}")

    # Agregar un StreamHandler si no hay logs configurados
    if not any(isinstance(h, logging.StreamHandler) for h in logging.getLogger().handlers):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(console_handler)

    print(f"stdout: {sys.stdout}, stderr: {sys.stderr}")

class SchedulerService(win32serviceutil.ServiceFramework):
    _svc_name_ = svc_name
    _svc_display_name_ = svc_display_name
    _svc_description_ = svc_description
    is_running = True
    path = find_root_directory()
    current_log_month = datetime.today().strftime("%Y-%b")

    def __init__(self, args):
        try:
            win32serviceutil.ServiceFramework.__init__(self, args)

            logs_folder = os.path.join(find_root_directory(), 'logs')

            if not os.path.exists(logs_folder):
                os.makedirs(logs_folder)

            logs_month_folder = os.path.join(logs_folder, self.current_log_month)

            if not os.path.exists(logs_month_folder):
                os.makedirs(logs_month_folder)

            debug_log_file = os.path.join(logs_month_folder, 'service_debug.log')
            error_log_file = os.path.join(logs_month_folder, 'service_error.log')

            configure_logging(debug_log_file, error_log_file)

            if len(args) > 1:  # Comprobamos si se proporcionó un argumento extra
                self.path = "".join(args[1:])  # El primer argumento es el nombre del servicio, el segundo será la ruta
                # Abrir el archivo en modo escritura
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        except Exception as e:
            logging.error(e)

    def SvcStop(self):
        self.is_running = False
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STOPPED, (self._svc_name_, ''))
        
    def SvcDoRun(self):
        try:
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ''))
            self.main()
        except Exception as e:
            logging.error(e)

    def main(self):
        logging.debug("Path: "+os.path.abspath(__file__))
        
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
                    logging.debug(f'Próxima ejecución: {job.next_run} - Hora actual: {datetime.now()} - Diferencia: {job.next_run - datetime.now()}')
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
                logging.error(f'Error al enviar actualización de icono: {e}')
            finally:
                job_running = False

    def reconfigure_logging_if_needed(self):
        new_month = datetime.today().strftime("%Y-%b")
        if new_month != self.current_log_month:
            # Remove existing handlers
            for handler in logging.getLogger().handlers[:]:
                if handler:
                    logging.getLogger().removeHandler(handler)
                    handler.close()
            
            # Create new log folder and files for the new month.
            logs_folder = os.path.join(find_root_directory(), 'logs')
            logs_month_folder = os.path.join(logs_folder, new_month)
            if not os.path.exists(logs_month_folder):
                os.makedirs(logs_month_folder)
            new_log_file = os.path.join(logs_month_folder, 'service_debug.log')
            error_log_file = os.path.join(logs_month_folder, 'service_error.log')
            
            # Reconfigure logging
            configure_logging(new_log_file, error_log_file)
            self.current_log_month = new_month

    def configure_schedule(self):
        '''
        Configure scheduled tasks based on the times loaded from the file.
        '''
        file_path = os.path.join(self.path, 'schedule.txt')
        
        logging.debug(not file_exists_in_folder('schedule.txt', file_path))
        if file_exists_in_folder('schedule.txt', file_path):
            # Path to the text file containing execution times
            file_path = os.path.join(find_root_directory(), 'schedule.txt')
        logging.debug(file_path)

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

        if manage_hours:
            # Iterate over execution times for manage_device_attendances
            for hour_to_perform in manage_hours:
                schedule.every().day.at(hour_to_perform).do(
                    lambda: safe_execute(manage_device_attendances, from_service=True)
                )

        if update_hours:
            # Iterate over execution times for update_device_time
            for hour_to_perform in update_hours:
                schedule.every().day.at(hour_to_perform).do(
                    lambda: safe_execute(update_devices_time, from_service=True)
                )
    
    def send_icon_update(self, color, host='localhost', port=5000):
        print("Envío de actualización de icono")
        # Create a TCP client socket to send the update message.
        try:
            client = original_socket.socket(original_socket.AF_INET, original_socket.SOCK_STREAM)
            client.connect((host, port))
            client.sendall(color.encode('utf-8'))
            client.close()
        except Exception as e:
            print(f"Error al enviar actualización: {e}")

def safe_execute(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except Exception as e:
        logging.error(f"Error ejecutando {func.__name__}: {e}")

def service_is_installed(service_name):
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
    
def check_and_install_service():
    if not service_is_installed(svc_name):
        # Install the service if it is not installed
        try:
            logging.debug(os.path.join(find_root_directory(), 'schedulerService.exe'))
            exe_name = None
            if os.path.isfile(os.path.join(find_root_directory(), 'schedulerService.exe')):
                exe_name = os.path.join(find_root_directory(), 'schedulerService.exe')
                logging.debug("EXE: "+exe_name)
            win32serviceutil.InstallService(pythonClassString=svc_python_class, serviceName=svc_name, displayName=svc_display_name, exeName=exe_name, description=svc_description, startType=win32service.SERVICE_AUTO_START)
            
        except Exception as e:
            logging.error(f'Error al instalar el servicio {svc_name}: {e}')
            return
        logging.info(f'Servicio {svc_name} instalado correctamente')
    else:
        logging.info(f'Servicio {svc_name} ya instalado')
        
if __name__ == "__main__":
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(SchedulerService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(SchedulerService)