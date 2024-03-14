import schedule
import time
import os
import subprocess
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
from tasks_device_manager import gestionar_marcaciones_dispositivos
from file_manager import cargar_desde_archivo
from utils import logging

class GestorRelojAsistencias(win32serviceutil.ServiceFramework):
    _svc_name_ = 'GestorRelojAsistencias'
    _svc_display_name_ = 'Gestor de Reloj De Asistencias'

    def __init__(self, args):
        logging.debug('Service initiated...')
        try:
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
            socket.setdefaulttimeout(60)
            self.is_alive = True
        except Exception as e:
            logging.error(e)

    def SvcStop(self):
        try:
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.hWaitStop)
            self.is_alive = False
        except Exception as e:
            logging.error(e)

    def SvcDoRun(self):
        try:
            logging.debug('Service started...')
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ''))
            self.main()
        except Exception as e:
            logging.error(e)

    def main(self):
        try:
            configurar_schedule()
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ''))
            while self.is_alive:
                logging.debug('Service executing...')
                schedule.run_pending()
                time.sleep(1)
        except Exception as e:
            raise(e)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(GestorRelojAsistencias)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(GestorRelojAsistencias)

def is_service_running():
    # Comando para verificar si el servicio está en ejecución
    result = subprocess.run(["sc.exe", "query", "GestorRelojAsistencias"], capture_output=True, text=True)
    logging.debug(result)
    return ("STATE" in result.stdout or "ESTADO" in result.stdout) and "RUNNING" in result.stdout

def configurar_schedule():
    '''
    Configura las tareas programadas en base a las horas cargadas desde el archivo.
    '''

    # Lee las horas de ejecución desde el archivo de texto
    filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schedule.txt')
    hoursToPerform = None
    try:
        hoursToPerform = cargar_desde_archivo(filePath)
    except Exception as e:
        logging.error(e)

    if hoursToPerform: 
        # Itera las horas de ejecución
        for hourToPerform in hoursToPerform:
            '''
            Ejecuta la tarea de actualizar hora y guardar las 
            marcaciones en archivos (individual y en conjunto)
            en la hora especificada en .at
            '''

            schedule.every().day.at(hourToPerform).do(gestionar_marcaciones_dispositivos)