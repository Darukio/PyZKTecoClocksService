from connection import *
from file_manager import *
from datetime import datetime
from errors import ConexionFallida, HoraDesactualizada
from utils import logging
import os

def organizar_info_dispositivos(line):
    # Dividir la línea en partes utilizando el separador " - "
    parts = line.strip().split(" - ")
    logging.debug(parts)
    # Verificar que hay exactamente 5 partes en la línea
    if len(parts) == 5:
        # Retorna un objeto con atributos
        return {
            "nombreDistrito": parts[0],
            "nombreModelo": parts[1],
            "puntoMarcacion": parts[2],
            "ip": parts[3],
            "activo": parts[4]
        }
    else:
        # Si no hay exactamente 5 partes, retornar None
        return None

def obtener_info_dispositivos(filePath):
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

def gestionar_marcaciones_dispositivos():
    # Obtiene la ubicación del archivo de texto
    filePath = os.path.join(os.path.abspath('.'), 'info_devices.txt')
    logging.debug(filePath)
    infoDevices = None
    try:
        # Obtiene todos los dispositivos en una lista formateada
        infoDevices = obtener_info_dispositivos(filePath)
    except Exception as e:
        logging.error(e)

    if infoDevices:
        # Itera a través de los dispositivos
        for infoDevice in infoDevices:
            try:
                # Si el dispositivo se encuentra activo...
                if eval(infoDevice["activo"]) == True:
                    conn = None
                    try:
                        conn = conectar(infoDevice["ip"], port=4370)
                    except Exception as e:
                        raise ConexionFallida(infoDevice["nombreModelo"], infoDevice["puntoMarcacion"], infoDevice["ip"]) from e
                    
                    if conn:
                        logging.info(f'Processing IP: {infoDevice["ip"]}')
                        actualizar_hora(conn)
                        attendances = obtener_marcaciones(conn)
                        logging.info(f'Attendances: {attendances}')
                        gestionar_marcaciones_individual(infoDevice, attendances)
                        gestionar_marcaciones_global(attendances)
                        finalizar_conexion(conn)
            except ConexionFallida as e:
                pass

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

def actualizar_hora_dispositivos():
    # Obtiene la ubicación del archivo de texto
    filePath = os.path.join(os.path.abspath('.'), 'info_devices.txt')
    logging.debug(filePath)
    infoDevices = None
    try:
        # Obtiene todos los dispositivos en una lista formateada
        infoDevices = obtener_info_dispositivos(filePath)
    except Exception as e:
        logging.error(e)

    if infoDevices:
        # Itera a través de los dispositivos
        for infoDevice in infoDevices:
            try:
                # Si el dispositivo se encuentra activo...
                if eval(infoDevice["activo"]) == True:
                    conn = None
                    try:
                        conn = conectar(infoDevice["ip"], port=4370)
                    except Exception as e:
                        raise ConexionFallida(infoDevice["nombreModelo"], infoDevice["puntoMarcacion"], infoDevice["ip"]) from e

                    if conn:
                        logging.info(f'Processing IP: {infoDevice["ip"]}')
                        try:
                            actualizar_hora(conn)
                        except Exception as e:
                            raise HoraDesactualizada(infoDevice["nombreModelo"], infoDevice["puntoMarcacion"], infoDevice["ip"]) from e
                        finalizar_conexion(conn)
            except ConexionFallida as e:
                pass
            except HoraDesactualizada as e:
                pass