from connection import *
from file_manager import *
from datetime import datetime
from errors import ConexionFallida
from utils import logging
import os

def organizar_info_dispositivos(line):
    # Dividir la línea en partes utilizando el separador " - "
    parts = line.strip().split(" - ")
    logging.debug(parts)
    # Verificar que hay exactamente 4 partes en la línea
    if len(parts) == 5:
        return {
            "nombreDistrito": parts[0],
            "nombreModelo": parts[1],
            "puntoMarcacion": parts[2],
            "ip": parts[3],
            "activo": parts[4]
        }
    else:
        # Si no hay exactamente 4 partes, retornar None
        return None

def obtener_info_dispositivos(filePath):
    dataList = cargar_desde_archivo(filePath)
    logging.debug(dataList)
    infoDevices = []
    for data in dataList:
        line = organizar_info_dispositivos(data)
        logging.debug(line)
        if line:
            infoDevices.append(line)
        logging.debug(infoDevices)
    return infoDevices

def gestionar_marcaciones_dispositivos():
    # Lee las IPs desde el archivo de texto
    filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'info_devices.txt')
    infoDevices = None
    try:
        infoDevices = obtener_info_dispositivos(filePath)
    except Exception as e:
        logging.error(e)

    if infoDevices:
        # Itera a través de las IPs
        for infoDevice in infoDevices:
            if eval(infoDevice["activo"]) == True:
                conn = None
                try:
                    conn = conectar(infoDevice["ip"], port=4370)
                except ConexionFallida as e:
                    logging.error(e)

                if conn:
                    logging.info(f'Processing IP: {infoDevice["ip"]}')
                    actualizar_hora(conn)
                    attendances = obtener_marcaciones(conn)
                    logging.info(f'Attendances: {attendances}')
                    gestionar_marcaciones_individual(infoDevice, attendances)
                    gestionar_marcaciones_global(attendances)
                    finalizar_conexion(conn)

def gestionar_marcaciones_individual(infoDevice, attendances):
    folderPath = crear_carpeta_y_devolver_ruta('devices', infoDevice["nombreDistrito"], infoDevice["nombreModelo"] + "-" + infoDevice["puntoMarcacion"])
    newtime = datetime.today().date()
    dateString = newtime.strftime("%Y-%m-%d")
    fileName = infoDevice["ip"]+'_'+dateString+'_file.cro'
    gestionar_guardado_de_marcaciones(attendances, folderPath, fileName)

def gestionar_marcaciones_global(attendances):
    folderPath = os.path.dirname(os.path.abspath(__file__))
    fileName = 'attendances_file.txt'
    gestionar_guardado_de_marcaciones(attendances, folderPath, fileName)

def gestionar_guardado_de_marcaciones(attendances, folderPath, fileName):
    destinyPath = os.path.join(folderPath, fileName)
    logging.debug(f'DestinyPath: {destinyPath}')
    guardar_marcaciones_en_archivo(attendances, destinyPath)

def actualizar_hora_dispositivos():
    # Lee las IPs desde el archivo de texto
    filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'info_devices.txt')
    infoDevices = None
    try:
        infoDevices = obtener_info_dispositivos(filePath)
    except Exception as e:
        logging.error(e)

    if infoDevices:
        # Itera a través de las IPs
        for infoDevice in infoDevices:
            if eval(infoDevice["activo"]) == True:
                conn = None
                try:
                    conn = conectar(infoDevice["ip"], port=4370)
                except ConexionFallida as e:
                    logging.error(e)

                if conn:
                    logging.info(f'Processing IP: {infoDevice["ip"]}')
                    actualizar_hora(conn)
                    finalizar_conexion(conn)