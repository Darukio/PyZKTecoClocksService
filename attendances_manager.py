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
from file_manager import *
from datetime import datetime
from errors import HoraDesactualizada
from utils import logging
import threading
import os

def gestionar_marcaciones_dispositivos():
    infoDevices = None
    try:
        # Obtiene todos los dispositivos en una lista formateada
        infoDevices = obtener_info_dispositivos()
    except Exception as e:
        logging.error(e)

    if infoDevices:
        threads = []
        # Itera a través de los dispositivos
        for infoDevice in infoDevices:
            # Si el dispositivo se encuentra activo...
            if eval(infoDevice["activo"]):
                conn = None
                    
                try:
                    conn = conectar(infoDevice["ip"], port=4370)
                except Exception as e:
                    thread = threading.Thread(target=reintentar_conexion_marcaciones_dispositivo, args=(infoDevice,))
                    thread.start()
                    threads.append(thread)

                gestionar_marcaciones_dispositivo(infoDevice, conn)

        # Espera a que todos los hilos hayan terminado
        if threads:
            for thread in threads:
                thread.join()

def gestionar_marcaciones_dispositivo(infoDevice, conn):
    if conn:
        logging.debug(conn)
        logging.debug(conn.get_platform())
        logging.debug(conn.get_device_name())
        logging.info(f'Processing IP: {infoDevice["ip"]}')
        try:
            try:
                actualizar_hora(conn)
            except Exception as e:
                raise HoraDesactualizada(infoDevice["nombreModelo"], infoDevice["puntoMarcacion"], infoDevice["ip"]) from e
        except HoraDesactualizada as e:
            pass
        attendances = obtener_marcaciones(conn)
        attendances = format_attendances(attendances, infoDevice["id"])
        logging.info(f'{infoDevice["ip"]} - Attendances: {attendances}')
        gestionar_marcaciones_individual(infoDevice, attendances)
        gestionar_marcaciones_global(attendances)
        finalizar_conexion(conn)
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

def reintentar_conexion_marcaciones_dispositivo(infoDevice):
    try:
        conn = reintentar_conexion(infoDevice)
        gestionar_marcaciones_dispositivo(infoDevice, conn)
    except Exception as e:
        pass
    return

def gestionar_marcaciones_individual(infoDevice, attendances):
    folderPath = crear_carpeta_y_devolver_ruta('devices', infoDevice["nombreDistrito"], infoDevice["nombreModelo"] + "-" + infoDevice["puntoMarcacion"])
    newtime = datetime.today().date()
    dateString = newtime.strftime("%Y-%m-%d")
    fileName = infoDevice["ip"]+'_'+dateString+'_file.cro'
    gestionar_guardado_de_marcaciones(attendances, folderPath, fileName)

def gestionar_marcaciones_global(attendances):
    folderPath = os.path.abspath('.')
    fileName = 'attendances_file.txt'
    gestionar_guardado_de_marcaciones(attendances, folderPath, fileName)

def gestionar_guardado_de_marcaciones(attendances, folderPath, fileName):
    destinyPath = os.path.join(folderPath, fileName)
    logging.debug(f'DestinyPath: {destinyPath}')
    guardar_marcaciones_en_archivo(attendances, destinyPath)

def obtener_cantidad_marcaciones():
    infoDevices = None
    try:
        # Obtiene todos los dispositivos en una lista formateada
        infoDevices = obtener_info_dispositivos()
    except Exception as e:
        logging.error(e)

    cantidad_marcaciones = {}
    intentos_maximos = 3

    if infoDevices:
        # Itera a través de los dispositivos
        for infoDevice in infoDevices:
            # Si el dispositivo se encuentra activo...
            if eval(infoDevice["activo"]) == True:
                conn = None

                intentos = 0

                while intentos < intentos_maximos:  # Intenta conectar hasta 3 veces
                    try:
                        conn = conectar(infoDevice['ip'], port=4370)
                        if conn:
                            break
                    except Exception as e:
                        logging.warning(f'Failed to connect to device {infoDevice['ip']}. Retrying...')
                        intentos += 1
                    
                if conn:
                    try:
                        conn.get_attendance()
                        cantidad_marcaciones[infoDevice["ip"]] = conn.records
                    except Exception as e:
                        cantidad_marcaciones[infoDevice["ip"]] = 'Conexión fallida'
                else:
                    cantidad_marcaciones[infoDevice["ip"]] = 'Conexión fallida'
                
    return cantidad_marcaciones