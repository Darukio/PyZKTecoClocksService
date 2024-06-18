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
from errors import HoraDesactualizada
from utils import logging
import threading

def actualizar_hora_dispositivos():
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
                    thread = threading.Thread(target=reintentar_conexion_hora, args=(infoDevice,))
                    thread.start()
                    threads.append(thread)

                actualizar_hora_dispositivo(infoDevice, conn)
    
        # Espera a que todos los hilos hayan terminado
        if threads:
            for thread in threads:
                thread.join()

def actualizar_hora_dispositivo(infoDevice, conn):
    if conn:
        logging.info(f'Processing IP: {infoDevice["ip"]}')
        try:
            try:
                actualizar_hora(conn)
            except Exception as e:
                raise HoraDesactualizada(infoDevice["nombreModelo"], infoDevice["puntoMarcacion"], infoDevice["ip"]) from e
        except HoraDesactualizada as e:
            pass
        finalizar_conexion(conn)
    return

def reintentar_conexion_hora(infoDevice):
    try:
        conn = reintentar_conexion(infoDevice)
        actualizar_hora_dispositivo(infoDevice, conn)
    except Exception as e:
        pass
    return