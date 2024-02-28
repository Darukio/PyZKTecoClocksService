from zk import ZK
import time
import os
from datetime import datetime
import configparser
'''
import schedule
import threading
import win32serviceutil
import win32service
import servicemanager
import socket
import win32timezone
import sys

class MyService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'MyService'
    _svc_display_name_ = 'My Service'

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.is_alive = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.is_alive = False

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ''))
        self.main()

    def main(self):
        while self.is_alive:
            schedule.run_pending()
            time.sleep(1)
'''

# Crear el objeto ConfigParser
config = configparser.ConfigParser()

# Leer el archivo config.ini
config.read('config.ini')

# Obtener el valor de la variable 'borrarMarcacionesDelReloj'
# borrarMarcaciones = config.getboolean('DEFAULT', 'borrarMarcacionesDelReloj', fallback=True)

def conectar(ip, port):
    zk = ZK(ip, port, timeout=5)
    try:
        print('Connecting to device ...')
        conn = zk.connect()
        print('Disabling device ...')
        conn.disable_device()
        conn.test_voice(index=10)
    except Exception as e:
        print(f'Process terminate : ', {e})
    finally:
        return conn
    
def actualizar_hora(conn):
    # get current machine's time
    zktime = conn.get_time()
    print(zktime)
    # update new time to machine
    newtime = datetime.today()
    conn.set_time(newtime)

def obtener_marcaciones(conn):
    attendances = []

    # Imprimir el valor actual
    # print(f'Valor actual de borrarMarcacionesDelReloj: {borrarMarcaciones}')
    try:
        print('Getting attendances ...')
        attendances = conn.get_attendance()
        conn.clear_attendance()
    except Exception as e:
        print(f'Process terminate : ', {e})
    finally:
        return attendances

def crear_carpeta_y_devolver_ruta(ip):
    # Directorio base donde se almacenarán las carpetas con la IP
    directorioActual = os.path.dirname(os.path.abspath(__file__))

    # Crear el directorio con la IP si no existe
    rutaDestino = os.path.join(directorioActual, ip)
    if not os.path.exists(rutaDestino):
        os.makedirs(rutaDestino)
        print(f"Se ha creado la carpeta {ip} en la ruta {directorioActual}")

    return rutaDestino

def guardar_marcaciones_en_archivo(attendances, file):
    try:
        with open(file, 'a') as f:
            for attendance in attendances:
                '''
                print('Attendance: ', attendance)
                print(dir(attendance))
                for attr_name, attr_value in vars(attendance).items():
                    print(f"{attr_name}: {type(attr_value)}")
                '''
                f.write(f"{attendance.user_id} {attendance.timestamp} {attendance.status} {attendance.punch}\n")
    except Exception as e:
        print(f'Process terminate : ', {e})

def main_job():
    # Lee las IPs desde el archivo de texto
    with open('file_ips.txt', 'r') as file_ips:
        lineas = file_ips.readlines()
        ips = [linea.strip() for linea in lineas]  # Elimina los saltos de línea

    # Itera a través de las IPs
    for ipDevice in ips:

        conn = None
        conn = conectar(ipDevice, port=4370)
        if conn:
            # FECHA
            newtime = datetime.today().date()
            dateString = newtime.strftime("%Y-%m-%d")
            print(f'Procesando IP: {ipDevice}, Fecha: {dateString}')
            actualizar_hora(conn)

            # CARPETA
            rutaCarpeta = crear_carpeta_y_devolver_ruta(ipDevice)
            
            # MARCACIONES
            attendancesFilePerDevice = ipDevice+'_'+dateString+'_file.cro'
            rutaDestino = os.path.join(rutaCarpeta, attendancesFilePerDevice)
            attendances = obtener_marcaciones(conn)
            print('Attendances: ', attendances)
            guardar_marcaciones_en_archivo(attendances, rutaDestino)

            attendancesFile = 'attendances_file.txt'
            rutaCarpeta = os.path.dirname(os.path.abspath(__file__))
            rutaDestino = os.path.join(rutaCarpeta, attendancesFile)
            guardar_marcaciones_en_archivo(attendances, rutaDestino)

            print('Enabling device ...')
            conn.enable_device()
            print('Disconnecting device ...')
            conn.disconnect()

'''
def main_job():
    conn = None
    ipDevice = '192.168.100.125'
    newtime = datetime.today().date()
    dateString = newtime.strftime("%Y-%m-%d")
    print(dateString)
    rutaCarpeta = crear_carpeta_y_devolver_ruta(ipDevice)
    attendancesFile = ipDevice+'_'+dateString+'_registro.cro'
    rutaDestino = os.path.join(rutaCarpeta, attendancesFile)
    conn = conectar(ipDevice, port=4370)
    if conn:
        actualizar_hora(conn)
        attendances = obtener_marcaciones(conn)
        guardar_marcaciones(attendances, rutaDestino)
        conn.enable_device()
        conn.disconnect()
'''
'''
def main():
    schedule.every().day.at("04:00").do(main_job)
    schedule.every().day.at("06:00").do(main_job)
    schedule.every().day.at("08:37").do(main_job)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(MyService)
        servicemanager.StartServiceCtrlDispatcher()
        print('hola')
    else:
        win32serviceutil.HandleCommandLine(MyService)
'''

if __name__ == '__main__':
    main_job()