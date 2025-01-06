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

from ..utils.errors import *
from ..utils.file_manager import *
import logging
import eventlet
from scripts import config
from .connection import *
from .device_manager import *
from .hour_manager import actualizar_hora_dispositivo
from datetime import datetime
import os
import threading
import eventlet
from eventlet.green import threading
import logging

class SharedState:
    def __init__(self):
        self.total_devices = 0
        self.processed_devices = 0
        self.lock = threading.Lock()

    def increment_processed_devices(self):
        with self.lock:
            self.processed_devices += 1
            return self.processed_devices

    def calculate_progress(self):
        with self.lock:
            if self.total_devices > 0:
                return int((self.processed_devices / self.total_devices) * 100)
            return 0

    def set_total_devices(self, total):
        with self.lock:
            self.total_devices = total

    def get_total_devices(self):
        return self.total_devices

def gestionar_marcaciones_dispositivos(desde_thread = False, emit_progress = None):
    logging.debug(f'desde_thread = {desde_thread}')
    info_devices = []
    try:
        # Obtiene todos los dispositivos en una lista formateada
        info_devices = obtener_info_dispositivos()
    except Exception as e:
        logging.error(e)

    results = {}

    if info_devices:
        gt = []
        info_devices_active = []
        config.read(os.path.join(encontrar_directorio_raiz(), 'config.ini'))
        coroutines_pool_max_size = int(config['Cpu_config']['coroutines_pool_max_size'])

        # Crea un pool de green threads
        pool = eventlet.GreenPool(coroutines_pool_max_size)
        state = SharedState()

        for info_device in info_devices:
            logging.debug(f'info_device["activo"]: {eval(info_device["activo"])} - desde_thread: {desde_thread}')
            if eval(info_device["activo"]) or desde_thread:
                logging.debug(f'info_device_active: {info_device}')
                info_devices_active.append(info_device)

        # Establece el total de dispositivos en el estado compartido
        state.set_total_devices(len(info_devices_active))
                
        for info_device_active in info_devices_active:
            try:
                gt.append(pool.spawn(gestionar_marcaciones_dispositivo, info_device_active, desde_thread, emit_progress, state))
            except Exception as e:
                pass
        
        for info_device_active, g in zip(info_devices_active, gt):
            logging.debug(f'Processing {info_device_active}')
            try:
                logging.debug(g)
                cant_marcaciones = g.wait()
            except Exception as e:
                logging.error(e)
                cant_marcaciones = 'Conexión fallida'

            # Guardar la información en results
            results[info_device_active["ip"]] = {
                "punto_marcacion": info_device_active["punto_marcacion"],
                "nombre_distrito": info_device_active["nombre_distrito"],
                "id": info_device_active["id"],
                "cant_marcaciones": str(cant_marcaciones)
            }
            logging.debug(results[info_device_active["ip"]])

        print('TERMINE MARCACIONES!')
        logging.debug('TERMINE MARCACIONES!')

    return results

def gestionar_marcaciones_dispositivo(info_device, p_desde_thread, emit_progress, state):
    try:
        try:
            attendances = reintentar_operacion_de_red(obtener_marcaciones, args=(info_device['ip'], 4370, info_device['communication'],), desde_thread=p_desde_thread)
            attendances = format_attendances(attendances, info_device["id"])
            logging.info(f'{info_device["ip"]} - Length attendances: {len(attendances)} - Attendances: {attendances}')
            
            gestionar_marcaciones_individual(info_device, attendances)
            gestionar_marcaciones_global(attendances)
        except IntentoConexionFallida as e:
            logging.debug(f'ConexionFallida {info_device["ip"]}')
            raise ConexionFallida(info_device['nombre_modelo'], info_device['punto_marcacion'], info_device['ip'])
        except Exception as e:
            raise e

        try:
            actualizar_hora_dispositivo(info_device)
        except Exception as e:
            logging.error(e)

        logging.debug(f'TERMINANDO MARCACIONES DISP {info_device["ip"]}')
        return len(attendances)
    except Exception as e:
        raise e
    finally:
        try:
            # Actualiza el número de dispositivos procesados y el progreso
            processed_devices = state.increment_processed_devices()
            if emit_progress:
                progress = state.calculate_progress()
                emit_progress(percent_progress=progress, device_progress=info_device["ip"], processed_devices=processed_devices, total_devices=state.get_total_devices())
                logging.debug(f"processed_devices: {processed_devices}/{state.get_total_devices()}, progress: {progress}%")
        except Exception as e:
            logging.error(e)

# Definir el mapeo de transformación
config.read(os.path.join(encontrar_directorio_raiz(), 'config.ini'))
attendance_status_dictionary = {
    1: config['Attendance_status']['status_fingerprint'],
    15: config['Attendance_status']['status_face'],
    0: config['Attendance_status']['status_card'],
    2: config['Attendance_status']['status_card'],
    4: config['Attendance_status']['status_card'],
}

# Función que aplica la transformación según el diccionario
def maping_dictionary(number):
    # Si el número está en el diccionario, retornar el valor transformado
    if number in attendance_status_dictionary:
        return attendance_status_dictionary[number]
    # Opcional: Manejar casos no especificados
    else:
        return 0

def format_attendances(attendances, id):
    formatted_attendances = []
    for attendance in attendances:
        formatted_timestamp = attendance.timestamp.strftime("%d/%m/%Y %H:%M") # Formatea el timestamp a DD/MM/YYYY hh:mm, ejemplo: 21/07/2023 05:28
        attendance_formatted = {
            "user_id": str(attendance.user_id).zfill(9),
            "timestamp": formatted_timestamp,
            "id": id,
            "status": maping_dictionary(int(attendance.status)),
        }
        formatted_attendances.append(attendance_formatted)
    return formatted_attendances

def gestionar_marcaciones_individual(info_device, attendances):
    folder_path = crear_carpeta_y_devolver_ruta('devices', info_device["nombre_distrito"], info_device["nombre_modelo"] + "-" + info_device["punto_marcacion"])
    new_time = datetime.today().date()
    date_string = new_time.strftime("%Y-%m-%d")
    file_name = info_device["ip"]+'_'+date_string+'_file.cro'
    gestionar_guardado_de_marcaciones(attendances, folder_path, file_name)

def gestionar_marcaciones_global(attendances):
    # Obtener el valor de name_attendances_file de la sección [Program_config]
    config.read(os.path.join(encontrar_directorio_raiz(), 'config.ini'))
    name_attendances_file = config['Program_config']['name_attendances_file']
    folder_path = encontrar_directorio_raiz()
    file_name = f"{name_attendances_file}.txt"
    gestionar_guardado_de_marcaciones(attendances, folder_path, file_name)

def gestionar_guardado_de_marcaciones(attendances, folder_path, file_name):
    destiny_path = os.path.join(folder_path, file_name)
    logging.debug(f'destiny_path: {destiny_path}')
    guardar_marcaciones_en_archivo(attendances, destiny_path)

def obtener_cantidad_marcaciones_dispositivos(emit_progress = None):
    info_devices = []
    try:
        # Obtiene todos los dispositivos en una lista formateada
        info_devices = obtener_info_dispositivos()
    except Exception as e:
        logging.error(e)

    results = {}

    if info_devices:
        gt = []
        info_devices_active = []
        config.read(os.path.join(encontrar_directorio_raiz(), 'config.ini'))
        coroutines_pool_max_size = int(config['Cpu_config']['coroutines_pool_max_size'])
        
        # Crea un pool de green threads
        pool = eventlet.GreenPool(coroutines_pool_max_size)
        for info_device in info_devices:
            if eval(info_device["activo"]):
                try:
                    gt.append(pool.spawn(obtener_cantidad_marcaciones_dispositivo, info_device))
                except Exception as e:
                    pass
                info_devices_active.append(info_device)

        for info_device_active, g in zip(info_devices_active, gt): 
            try:
                cant_marcaciones = g.wait()
            except Exception as e:
                logging.error(e)
                cant_marcaciones = 'Conexión fallida'
                    
            # Guardar la información en results
            results[info_device_active["ip"]] = {
                "punto_marcacion": info_device_active["punto_marcacion"],
                "nombre_distrito": info_device_active["nombre_distrito"],
                "id": info_device_active["id"],
                "cant_marcaciones": str(cant_marcaciones)
            }
            logging.debug(results[info_device_active["ip"]])

        #failed_connections = {ip: info for ip, info in results.items() if info["status"] == "Conexión fallida"}
        print('TERMINE CANT MARCACIONES!')
        logging.debug('TERMINE CANT MARCACIONES!')

    return results

def obtener_cantidad_marcaciones_dispositivo(info_device):
    try:
        records = reintentar_operacion_de_red(obtener_cantidad_marcaciones, args=(info_device["ip"], 4370, info_device['communication'],))
        logging.debug(f'IP: {info_device["ip"]} - Records: {records}')
        return records
    except IntentoConexionFallida as e:
        raise ConexionFallida(info_device['nombre_modelo'], info_device['punto_marcacion'], info_device['ip'])
    except Exception as e:
        raise e

    return