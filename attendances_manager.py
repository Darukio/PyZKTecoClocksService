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

from connection import *
from device_manager import *
from hour_manager import actualizar_hora_dispositivo
from file_manager import *
from datetime import datetime
from errors import *
from utils import logging
import os
import configparser
import eventlet

# Para leer un archivo INI
config = configparser.ConfigParser()

def gestionar_marcaciones_dispositivos():
    info_devices = []
    try:
        # Obtiene todos los dispositivos en una lista formateada
        info_devices = obtener_info_dispositivos()
    except Exception as e:
        logging.error(e)
        
    if info_devices:
        gt = []
        config.read('config.ini')
        coroutines_pool_max_size = int(config['Cpu_config']['coroutines_pool_max_size'])
        # Crea un pool de green threads
        pool = eventlet.GreenPool(coroutines_pool_max_size)
        
        for info_device in info_devices:
            # Si el dispositivo se encuentra activo...
            if eval(info_device["activo"]):
                # Lanza una corutina para cada dispositivo activo
                gt.append(pool.spawn(gestionar_marcaciones_dispositivo, info_device))
        
        # Espera a que todas las corutinas en el pool hayan terminado
        for g in gt:
            try:
                g.wait()
            except Exception as e:
                logging.error(e)
        
        print('TERMINE MARCACIONES!')
        logging.debug('TERMINE MARCACIONES!')

def gestionar_marcaciones_dispositivo(info_device):
    try:
        attendances = reintentar_operacion_de_red(obtener_marcaciones, args=(info_device['ip'], 4370,))
        attendances = format_attendances(attendances, info_device["id"])
        logging.info(f'{info_device["ip"]} - Attendances: {attendances}')
        
        gestionar_marcaciones_individual(info_device, attendances)
        gestionar_marcaciones_global(attendances)
    except IntentoConexionFallida as e:
        raise ConexionFallida(info_device['nombre_modelo'], info_device['punto_marcacion'], info_device['ip'])
    except Exception as e:
        raise e

    actualizar_hora_dispositivo(info_device)

    return

def format_attendances(attendances, id):
    formatted_attendances = []
    for attendance in attendances:
        formatted_timestamp = attendance.timestamp.strftime("%d/%m/%Y %H:%M") # Formatea el timestamp a DD/MM/YYYY hh:mm, ejemplo: 21/07/2023 05:28
        attendance_formatted = {
            "user_id": attendance.user_id,
            "timestamp": formatted_timestamp,
            "id": id,
            "status": attendance.status
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
    folder_path = os.path.abspath('.')
    file_name = 'attendances_file.txt'
    gestionar_guardado_de_marcaciones(attendances, folder_path, file_name)

def gestionar_guardado_de_marcaciones(attendances, folder_path, file_name):
    destiny_path = os.path.join(folder_path, file_name)
    logging.debug(f'DestinyPath: {destiny_path}')
    guardar_marcaciones_en_archivo(attendances, destiny_path)

def obtener_cantidad_marcaciones_dispositivos():
    info_devices = []
    try:
        # Obtiene todos los dispositivos en una lista formateada
        info_devices = obtener_info_dispositivos()
    except Exception as e:
        logging.error(e)

    cantidad_marcaciones = {}

    if info_devices:
        cantidad_marcaciones = {}
        info_devices_active = []
        gt = []
        config.read('config.ini')
        coroutines_pool_max_size = int(config['Cpu_config']['coroutines_pool_max_size'])
        # Crea un pool de green threads
        pool = eventlet.GreenPool(coroutines_pool_max_size)
        
        for info_device in info_devices:
            # Si el dispositivo se encuentra activo...
            if eval(info_device["activo"]):
                # Lanza una corutina para cada dispositivo activo
                gt.append(pool.spawn(obtener_cantidad_marcaciones_dispositivo, info_device))
                info_devices_active.append(info_device)

        # Espera a que todas las corutinas en el pool hayan terminado
        for info_device_active, g in zip(info_devices_active, gt):
            try:
                cantidad_marcaciones[info_device_active["ip"]] = g.wait()
            except Exception as e:
                cantidad_marcaciones[info_device_active["ip"]] = 'Conexión fallida'

        print('TERMINE CANT MARCACIONES!')
        logging.debug('TERMINE CANT MARCACIONES!')

    return cantidad_marcaciones

def obtener_cantidad_marcaciones_dispositivo(info_device):
    try:
        records = reintentar_operacion_de_red(obtener_cantidad_marcaciones, args=(info_device["ip"], 4370,))
        logging.debug(f'IP: {info_device["ip"]} - Records: {records}')
        return records
    except IntentoConexionFallida as e:
        raise ConexionFallida(info_device['nombre_modelo'], info_device['punto_marcacion'], info_device['ip'])
    except Exception as e:
        raise e

    return