import eventlet
eventlet.monkey_patch()

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

from scripts.business_logic.attendances_manager import manage_device_attendances
from scripts.business_logic.hour_manager import update_device_time
from scripts.utils.file_manager import file_exists_in_folder, find_root_directory, load_from_file

svc_python_class = "schedulerService.SchedulerService"
svc_name = "GESTOR_RELOJ_ASISTENCIA"
svc_display_name = "GESTOR RELOJ DE ASISTENCIAS"
svc_description = "Servicio para sincronización de tiempo y recuperación de datos de asistencia."

locale.setlocale(locale.LC_TIME, "Spanish_Argentina.1252")  # Español de Argentina

class OperationThread(QThread):
    def __init__(self, operation_function, parent=None):
        super().__init__(parent)
        self.operation_function = operation_function

    def run(self):
        try:
            self.operation_function(from_service=True)
        except Exception as e:
            logging.critical(e)

class SchedulerService(win32serviceutil.ServiceFramework):
    _svc_name_ = svc_name
    _svc_display_name_ = svc_display_name
    _svc_description_ = svc_description
    is_running = True
    path = find_root_directory()

    def __init__(self, args):
        try:
            win32serviceutil.ServiceFramework.__init__(self, args)

            logs_folder = os.path.join(self.path, 'logs')

            # Crear la carpeta logs si no existe
            if not os.path.exists(logs_folder):
                os.makedirs(logs_folder)

            new_time = datetime.today().date()
            date_string = new_time.strftime("%Y-%b")
            logs_month_folder = os.path.join(logs_folder, date_string)

            # Crear la carpeta logs_month si no existe
            if not os.path.exists(logs_month_folder):
                os.makedirs(logs_month_folder)

            debug_log_file = os.path.join(logs_month_folder, 'scheduler_debug.log')
            # Configurar el sistema de registros básico para program_debug.log
            logging.basicConfig(filename=debug_log_file, level=logging.DEBUG,
                                format='%(asctime)s - %(levelname)s - %(message)s')

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
        print('Starting Service...')
        
        logging.debug("Path: "+os.path.abspath(__file__))
        print("Path: "+os.path.abspath(__file__))
        
        try:
            self.configure_schedule()
        except Exception as e:
            logging.error(e)
        
        try:
            logging.debug(f'Tareas programadas: {str(len(schedule.get_jobs()))}\n{str(schedule.get_jobs())}')
            while self.is_running:
                logging.debug('Ejecutando tarea programada...')
                self.ReportServiceStatus(win32service.SERVICE_RUNNING)
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            # Manejar la interrupción del teclado (Ctrl + C)
            logging.error('Interrupción de teclado detectada, deteniendo el servicio...')
            self.SvcStop()
        except Exception as e:
            logging.error('Error inesperado: %s', e)
            self.SvcStop()

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
                schedule.every().day.at(hour_to_perform).do(manage_device_attendances, from_service=True)

        if update_hours:
            # Iterate over execution times for update_device_time
            for hour_to_perform in update_hours:
                schedule.every().day.at(hour_to_perform).do(update_device_time, from_service=True)

def create_operation_thread(operation_function):
    '''
    Create a thread to execute an operation.
    '''
    thread = OperationThread(operation_function)
    thread.start()

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
            logging.error("Servicio no instalado")
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
            logging.debug(os.path.isfile(os.path.join(find_root_directory(), 'schedulerService.exe')))
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