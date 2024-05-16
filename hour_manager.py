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

                actualizar_hora_dispositivo(infoDevice, conn)

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
    conn = reintentar_conexion(infoDevice)
    actualizar_hora_dispositivo(infoDevice, conn)
    return