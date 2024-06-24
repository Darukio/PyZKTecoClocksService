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

import threading
import queue
from connection import *
from file_manager import *
from errors import ConexionFallida
from utils import logging

def organizar_info_dispositivos(line):
    # Dividir la línea en partes utilizando el separador " - "
    parts = line.strip().split(" - ")
    logging.debug(parts)
    # Verificar que hay exactamente 6 partes en la línea
    if len(parts) == 6:
        # Retorna un objeto con atributos
        return {
            "nombreDistrito": parts[0],
            "nombreModelo": parts[1],
            "puntoMarcacion": parts[2],
            "ip": parts[3],
            "id": parts[4],
            "activo": parts[5]
        }
    else:
        # Si no hay exactamente 6 partes, retornar None
        return None

def obtener_info_dispositivos():
    # Obtiene la ubicación del archivo de texto
    filePath = os.path.join(os.path.abspath('.'), 'info_devices.txt')
    logging.debug(filePath)
    # Obtiene la info de dispositivos de info_devices.txt
    dataList = cargar_desde_archivo(filePath)
    logging.debug(dataList)
    infoDevices = []
    # Itera los distintos dispositivos
    for data in dataList:
        # A la línea sin formatear, crea un objeto de dispositivo
        line = organizar_info_dispositivos(data)
        logging.debug(line)
        if line:
            # Anexa el dispositivo a la lista de dispositivos
            infoDevices.append(line)
        logging.debug(infoDevices)
    return infoDevices

def reintentar_conexion(infoDevice):
    conn = None
    logging.info(f'Retrying connection to device {infoDevice["ip"]}...')
    intentos_maximos = 3
    intentos = 0
    while intentos < intentos_maximos:  # Intenta conectar hasta 3 veces
        try:
            conn = conectar(infoDevice['ip'], port=4370)
            return conn
        except Exception as e:
            logging.warning(f'Failed to connect to device {infoDevice['ip']}. Retrying...')
            intentos += 1
    logging.error(f'Unable to connect to device {infoDevice['ip']} after {intentos} attempts.')    
    raise ConexionFallida(infoDevice['nombreModelo'], infoDevice['puntoMarcacion'], infoDevice['ip'])

def ping_devices():
    infoDevices = None
    try:
        # Obtiene todos los dispositivos en una lista formateada
        infoDevices = obtener_info_dispositivos()
        logging.debug(infoDevices)
    except Exception as e:
        logging.error(e)

    results = {}
    results_queue = queue.Queue()
    if infoDevices:
        threads = []
        # Itera a través de los dispositivos
        for infoDevice in infoDevices:
            # Si el dispositivo se encuentra activo...
            if eval(infoDevice["activo"]):
                conn = None
                    
                try:
                    conn = conectar(infoDevice["ip"], port=4370)
                    results[infoDevice["ip"]] = "Conexión exitosa"
                    finalizar_conexion(conn)
                except Exception as e:
                    try:
                        thread = threading.Thread(target=reintentar_ping_device, args=(infoDevice,results_queue,))
                        thread.start()
                        threads.append(thread)
                    except Exception as e:
                        logging.error(e)

        # Espera a que todos los hilos hayan terminado
        if threads:
            logging.debug(threads)
            for thread in threads:
                thread.join()
        
        logging.debug(results)
        # Procesar los resultados de la cola
        while not results_queue.empty():
            result = results_queue.get()
            logging.debug(result)
            logging.debug(f'{result["ip"]} - {result["status"]}')
            ip = result["ip"]
            status = result["status"]
            results[ip] = status

    return results

def reintentar_ping_device(infoDevice, results_queue):
    try:
        conn = reintentar_conexion(infoDevice)
        results_queue.put({"ip": infoDevice["ip"], "status": "Conexión exitosa"})
        logging.debug(f'{"ip": infoDevice["ip"], "status": "Conexión exitosa"}')
        finalizar_conexion(conn)
    except Exception as e:
        results_queue.put({"ip": infoDevice["ip"], "status": "Conexión fallida"})
        logging.debug(f'{"ip": infoDevice["ip"], "status": "Conexión fallida"}')
    return