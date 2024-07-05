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
from errors import *
from file_manager import *
from utils import logging
import configparser
import time
import os
import eventlet

# Para leer un archivo INI
config = configparser.ConfigParser()

def organizar_info_dispositivos(line):
    # Dividir la línea en partes utilizando el separador " - "
    parts = line.strip().split(" - ")
    logging.debug(parts)
    # Verificar que hay exactamente 6 partes en la línea
    if len(parts) == 6:
        # Retorna un objeto con atributos
        return {
            "nombre_distrito": parts[0],
            "nombre_modelo": parts[1],
            "punto_marcacion": parts[2],
            "ip": parts[3],
            "id": parts[4],
            "activo": parts[5]
        }
    else:
        # Si no hay exactamente 6 partes, retornar None
        return None

def obtener_info_dispositivos():
    # Obtiene la ubicación del archivo de texto
    file_path = os.path.join(os.path.abspath('.'), 'info_devices.txt')
    logging.debug(file_path)
    # Obtiene la info de dispositivos de info_devices.txt
    data_list = cargar_desde_archivo(file_path)
    logging.debug(data_list)
    info_devices = []
    # Itera los distintos dispositivos
    for data in data_list:
        # A la línea sin formatear, crea un objeto de dispositivo
        line = organizar_info_dispositivos(data)
        logging.debug(line)
        if line:
            # Anexa el dispositivo a la lista de dispositivos
            info_devices.append(line)
        logging.debug(info_devices)
    return info_devices

def ping_devices():
    info_devices = None
    try:
        # Obtiene todos los dispositivos en una lista formateada
        info_devices = obtener_info_dispositivos()
        logging.debug(info_devices)
    except Exception as e:
        logging.error(e)

    results = {}
    failed_connections = {}
    if info_devices:
        # Itera a través de los dispositivos
        for info_device in info_devices:
            # Si el dispositivo se encuentra activo...
            if eval(info_device["activo"]):
                conn = None
                status = None
                
                result_ping = ping_device(info_device["ip"], 4370)
                if result_ping:
                    status = "Conexión exitosa"
                else:
                    status = "Conexión fallida"                    
                
                # Guardar la información en results
                results[info_device["ip"]] = {
                    "punto_marcacion": info_device["punto_marcacion"],
                    "nombre_distrito": info_device["nombre_distrito"],
                    "id": info_device["id"],
                    "status": status
                }
                logging.debug(results[info_device["ip"]])

        failed_connections = {ip: info for ip, info in results.items() if info["status"] == "Conexión fallida"}

    return failed_connections

def reintentar_operacion_de_red(op, args=(), kwargs={}, intentos_maximos=3):
    config.read('config.ini')
    intentos_maximos = int(config['Network_config']['retry_connection'])
    result = None
    conn = None

    for _ in range(intentos_maximos):
        try:
            if conn is None:
                conn = conectar(*args, **kwargs)
            result = op(conn)
            finalizar_conexion(conn)
            break
        except HoraValidacionFallida as e:
            raise e
        except IntentoConexionFallida as e:
            conn = None
            logging.warning(f"Failed attempt {_ + 1} of {intentos_maximos} for operation {op.__name__}: {e.__cause__}")
            if result:
                break
            if _ + 1 == intentos_maximos:
                raise e
            eventlet.sleep(0)
    
    return result