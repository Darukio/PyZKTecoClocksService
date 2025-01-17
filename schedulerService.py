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

from scripts.business_logic.attendances_manager import gestionar_marcaciones_dispositivos
from scripts.business_logic.hour_manager import actualizar_hora_dispositivos
from scripts.utils.file_manager import cargar_desde_archivo, encontrar_directorio_raiz, existe_archivo_en_carpeta

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
    path = encontrar_directorio_raiz()

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
            self.configurar_schedule()
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

    def configurar_schedule(self):
        '''
        Configurar las tareas programadas en base a las horas cargadas desde el archivo.
        '''
        file_path = os.path.join(self.path, 'schedule.txt')
        
        logging.debug(not existe_archivo_en_carpeta('schedule.txt', file_path))
        if existe_archivo_en_carpeta('schedule.txt', file_path):
            # Ruta del archivo de texto que contiene las horas de ejecución
            file_path = os.path.join(encontrar_directorio_raiz(), 'schedule.txt')
        logging.debug(file_path)

        try:
            content = cargar_desde_archivo(file_path)  # Cargar contenido desde el archivo
        except Exception as e:
            logging.error(e)  # Registro de error si falla la operación
            return

        gestionar_hours = []
        actualizar_hours = []
        current_task = None

        for line in content:
            if line.startswith("#"):
                if "gestionar_marcaciones_dispositivos" in line:
                    current_task = "gestionar"
                elif "actualizar_hora_dispositivos" in line:
                    current_task = "actualizar"
            elif line:
                if current_task == "gestionar":
                    gestionar_hours.append(line)
                elif current_task == "actualizar":
                    actualizar_hours.append(line)

        if gestionar_hours:
            # Iterar las horas de ejecución para gestionar_marcaciones_dispositivos
            for hour_to_perform in gestionar_hours:
                # schedule.every().day.at(hour_to_perform).do(self.thread_gestionar_marcaciones_dispositivos)
                schedule.every().day.at(hour_to_perform).do(gestionar_marcaciones_dispositivos, desde_service=True)

        if actualizar_hours:
            # Iterar las horas de ejecución para actualizar_hora_dispositivos
            for hour_to_perform in actualizar_hours:
                # schedule.every().day.at(hour_to_perform).do(self.thread_actualizar_hora_dispositivos)
                schedule.every().day.at(hour_to_perform).do(actualizar_hora_dispositivos, desde_service=True)

def service_is_installed(service_name):
    try:
        # Abre el gestor de control de servicios
        scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
        try:
            # Intenta abrir el servicio
            servicio = win32service.OpenService(scm, service_name, win32service.SERVICE_QUERY_STATUS)
            # Si se puede abrir, el servicio está instalado
            win32service.CloseServiceHandle(servicio)
            return True
        except win32service.error as e:
            # Si el error es ERROR_SERVICE_DOES_NOT_EXIST, el servicio no está instalado
            logging.error("Servicio no instalado")
            return False
        finally:
            win32service.CloseServiceHandle(scm)
    except Exception as e:
        print(f"Error al verificar el servicio: {e}")
        return False
    
def check_and_install_service():
    if not service_is_installed(svc_name):
        # Instalar el servicio si no está instalado
        try:
            logging.debug(os.path.join(encontrar_directorio_raiz(), 'schedulerService.exe'))
            logging.debug(os.path.isfile(os.path.join(encontrar_directorio_raiz(), 'schedulerService.exe')))
            exe_name = None
            if os.path.isfile(os.path.join(encontrar_directorio_raiz(), 'schedulerService.exe')):
                exe_name = os.path.join(encontrar_directorio_raiz(), 'schedulerService.exe')
                logging.debug("EXE: "+exe_name)
            win32serviceutil.InstallService(pythonClassString=svc_python_class, serviceName=svc_name, displayName=svc_display_name, exeName=exe_name, description=svc_description, startType=win32service.SERVICE_AUTO_START)
            
        except Exception as e:
            logging.error(f'Error al instalar el servicio {svc_name}: {e}')
            return
        #subprocess.run(['sc', 'create', svc_name, 'binPath= "' + svc_script + '"'])
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