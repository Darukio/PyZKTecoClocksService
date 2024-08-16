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
import os
from scripts import config
from .connection import *
import time
from scripts import config

def organizar_info_dispositivos(line):
    # Dividir la línea en partes utilizando el separador " - "
    parts = line.strip().split(" - ")
    logging.debug(parts)
    # Verificar que hay exactamente 6 partes en la línea
    if len(parts) == 7:
        # Retorna un objeto con atributos
        return {
            "nombre_distrito": parts[0],
            "nombre_modelo": parts[1],
            "punto_marcacion": parts[2],
            "ip": parts[3],
            "id": parts[4],
            "communication": parts[5],
            "activo": parts[6]
        }
    else:
        # Si no hay exactamente 6 partes, retornar None
        return None

def obtener_info_dispositivos():
    # Obtiene la ubicación del archivo de texto
    file_path = os.path.join(encontrar_directorio_raiz(), 'info_devices.txt')
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
                    gt.append(pool.spawn(ping_device, info_device["ip"], 4370))
                except Exception as e:
                    pass
                info_devices_active.append(info_device)

        for info_device_active, g in zip(info_devices_active, gt):
            response = g.wait()
            if response:
                status = "Conexión exitosa"
            else:
                status = "Conexión fallida"

            # Guardar la información en results
            results[info_device_active["ip"]] = {
                "punto_marcacion": info_device_active["punto_marcacion"],
                "nombre_distrito": info_device_active["nombre_distrito"],
                "id": info_device_active["id"],
                "status": status
            }
            logging.debug(results[info_device_active["ip"]])

        #failed_connections = {ip: info for ip, info in results.items() if info["status"] == "Conexión fallida"}
        print('TERMINE PING!')
        logging.debug('TERMINE PING!')

    return results

def reintentar_operacion_de_red(op, args=(), kwargs={}, intentos_maximos=3, desde_thread = False):
    config.read(os.path.join(encontrar_directorio_raiz(), 'config.ini'))
    intentos_maximos = int(config['Network_config']['retry_connection'])
    result = None
    conn = None

    for _ in range(intentos_maximos):
        try:
            logging.debug(f'{args} CONNECTING!')
            if conn is None:
                conn = conectar(*args, **kwargs)
            logging.debug(f'{args} OPERATION!')
            result = op(conn, desde_thread)
            logging.debug(f'{args} ENDING!')
            finalizar_conexion(conn, *args)
            logging.debug(f'{args} ENDED!')
            break
        except HoraValidacionFallida as e:
            raise e
        except IntentoConexionFallida as e:
            conn = None
            logging.warning(f"{e} - Failed attempt {_ + 1} of {intentos_maximos} for operation {op.__name__}: {e.__cause__}")
            if result:
                break
            if _ + 1 == intentos_maximos:
                raise e
            eventlet.sleep(0)
        except Exception as e:
            logging.error(e)
            pass
                
    logging.debug(f'{args} RESULT!')
    return result