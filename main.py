from connection import *
from manejo_de_archivos import *
from datetime import datetime
import schedule
import sys
import time
import os
import subprocess
import threading
import win32serviceutil
import win32service
import win32event
import pyuac
import servicemanager
import socket
from pystray import MenuItem as item
from pystray import Icon, Menu
from PIL import Image

# Variables globales
logPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'service_log.txt')

class MyService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'MyService'
    _svc_display_name_ = 'My Service'

    def __init__(self, args):
        with open(logPath, 'a') as logFile:
            logFile.write("Service initiated...\n")
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_alive = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False

    def SvcDoRun(self):
        with open(logPath, 'a') as logFile:
            logFile.write("Service started...\n")
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ''))
        self.main()

    def main(self):
        configurar_schedule()
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ''))
        while self.is_alive:
            
            with open(logPath, 'a') as logFile:
                logFile.write("Service executing...\n")
            schedule.run_pending()
            time.sleep(1)

def main_job():
    # Lee las IPs desde el archivo de texto
    filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'file_ips.txt')
    ips = cargar_desde_archivo(filePath)
        
    # Itera a través de las IPs
    for ipDevice in ips:
        conn = None
        try:
            with open(logPath, 'a') as logFile:
                logFile.write(f'Service connecting with device {ipDevice}...\n')
            conn = conectar(ipDevice, port=4370)
        except Exception as e:
            folderPath = crear_carpeta_y_devolver_ruta(ipDevice)
            newtime = datetime.today().date()
            dateString = newtime.strftime("%Y-%m-%d")
            fileName = ipDevice+'_'+dateString+'_logs.txt'
            filePath = os.path.join(folderPath, fileName)
            with open(filePath, 'a') as file:
                file.write(f'Connection failed with device {ipDevice}: ', e)

        if conn:
            # FECHA
            newtime = datetime.today().date()
            dateString = newtime.strftime("%Y-%m-%d")
            print(f'Processing IP: {ipDevice}, Date: {dateString}')
            actualizar_hora(conn)

            # CARPETA
            folderPath = crear_carpeta_y_devolver_ruta(ipDevice)
                
            # MARCACIONES
            fileName = ipDevice+'_'+dateString+'_file.cro'
            destinyPath = os.path.join(folderPath, fileName)
            attendances = obtener_marcaciones(conn)
            print('Attendances: ', attendances)
            guardar_marcaciones_en_archivo(attendances, destinyPath)

            fileName = 'attendances_file.txt'
            folderPath = os.path.dirname(os.path.abspath(__file__))
            destinyPath = os.path.join(folderPath, fileName)
            guardar_marcaciones_en_archivo(attendances, destinyPath)

            print('Enabling device...')
            conn.enable_device()
            print('Disconnecting device...')
            conn.disconnect()

def configurar_schedule():
    '''
    Configura las tareas programadas en base a las horas cargadas desde el archivo.
    '''

    # Lee las horas de ejecución desde el archivo de texto
    filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schedule.txt')
    hoursToPerform = cargar_desde_archivo(filePath)
        
    # Itera las horas de ejecución
    for hourToPerform in hoursToPerform:
        '''
        Ejecuta la tarea de actualizar hora y guardar las 
        marcaciones en archivos (individual y en conjunto)
        en la hora especificada en .at
        '''

        schedule.every().day.at(hourToPerform).do(main_job)

def exit_icon(icon, item):
    stop_service(icon)
    icon.stop()

def start_service(icon):
    if pyuac.isUserAdmin():
        set_icon_color(icon, "green")
        subprocess.run(["net", "start", "MyService"], shell=True)

def stop_service(icon):
    set_icon_color(icon, "red")
    subprocess.run(["net", "stop", "MyService"], shell=True)

def set_icon_color(icon, color):
    # Función para cambiar el color del ícono
    filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", f"circle-{color}.png")
    image = Image.open(filePath)
    icon.update_menu()
    icon.icon = image

def restart_service(icon):
    stop_service(icon)
    start_service(icon)

def item_actualizar_hora(icon, item):
    # Lee las IPs desde el archivo de texto
    filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'file_ips.txt')
    ips = cargar_desde_archivo(filePath)
        
    # Itera a través de las IPs
    for ipDevice in ips:
        conn = None
        with open(logPath, 'a') as logFile:
            logFile.write(f'Service trying to connect with device {ipDevice}...\n')
        try:
            conn = conectar(ipDevice, port=4370)
        except Exception as e:
            folderPath = crear_carpeta_y_devolver_ruta(ipDevice)
            newtime = datetime.today().date()
            dateString = newtime.strftime("%Y-%m-%d")
            fileName = ipDevice+'_'+dateString+'_logs.txt'
            filePath = os.path.join(folderPath, fileName)
            with open(filePath, 'a') as file:
                file.write(f'Connection failed with device {ipDevice}: {e.args}')
        if conn:
            # FECHA
            newtime = datetime.today().date()
            dateString = newtime.strftime("%Y-%m-%d")
            print(f'Processing IP: {ipDevice}, Date: {dateString}')
            actualizar_hora(conn)

            print('Enabling device...')
            conn.enable_device()
            print('Disconnecting device...')
            conn.disconnect()

# Crear ícono en la bandeja del sistema
def create_tray_icon():
    initial_color = "green" if is_service_running() else "red"
    filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", f"circle-{initial_color}.png")
    image = Image.open(filePath)

    icon = Icon("MyService", image, "Gestor de Reloj de Asistencias", menu=Menu(
        item('Iniciar', start_service),
        item('Detener', stop_service),
        item('Actualizar hora', item_actualizar_hora),
        item('Obtener marcaciones', main_job),
        item('Salir', exit_icon)
    ))

    return icon

def is_service_running():
    # Comando para verificar si el servicio está en ejecución
    result = subprocess.run(["sc", "query", "MyService"], capture_output=True, text=True)
    return "STATE" in result.stdout or "ESTADO" in result.stdout and "RUNNING" in result.stdout

@pyuac.main_requires_admin
def main():
    with open(logPath, 'a') as logFile:
        logFile.write('Script executing...\n')

    logFilePath = 'console_log.txt'

    # Redirigir salida estándar y de error al archivo de registro
    sys.stdout = open(logFilePath, 'a')
    sys.stderr = open(logFilePath, 'a')

    if len(sys.argv) == 1:
        tray_icon = create_tray_icon()
        tray_icon.run()
        # servicemanager.Initialize()
        # servicemanager.PrepareToHostSingle(MyService)
        # servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(MyService)

if __name__ == '__main__':
    main()


#threading.Thread(target=tray_icon.run).start()
#systernals paquete de wind
'''
if __name__ == '__main__':
    with open(logPath, 'a') as logFile:
        logFile.write('Script executing...\n')

    logFilePath = 'console_log.txt'

    # Redirigir salida estándar y de error al archivo de registro
    sys.stdout = open(logFilePath, 'a')
    sys.stderr = open(logFilePath, 'a')

    print(sys.argv)

    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(MyService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(MyService)
'''