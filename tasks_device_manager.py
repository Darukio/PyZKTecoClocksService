from connection import *
from file_manager import *
from datetime import datetime
from errors import ConexionFallida, HoraDesactualizada
from utils import logging
import threading
import os

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
            # Si el dispositivo se encuentra activo...
            if eval(infoDevice["activo"]) == True:
                conn = None
                    
                try:
                    conn = conectar(infoDevice["ip"], port=4370)
                except Exception as e:
                    thread = threading.Thread(target=reintentar_conexion_marcaciones, args=(infoDevice,))
                    thread.start()

                gestionar_marcaciones_conexion(infoDevice, conn)

def gestionar_marcaciones_conexion(infoDevice, conn):
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

def reintentar_conexion_marcaciones(infoDevice):
    conn = reintentar_conexion(infoDevice)
    gestionar_marcaciones_conexion(infoDevice, conn)
    return

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
    try:    
        raise ConexionFallida(infoDevice['nombreModelo'], infoDevice['puntoMarcacion'], infoDevice['ip'])
    except ConexionFallida:
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
            # Si el dispositivo se encuentra activo...
            if eval(infoDevice["activo"]) == True:
                conn = None
                        
                try:
                    conn = conectar(infoDevice["ip"], port=4370)
                except Exception as e:
                    thread = threading.Thread(target=reintentar_conexion_hora, args=(infoDevice,))
                    thread.start()

                actualizar_hora_conexion(infoDevice, conn)

def reintentar_conexion_hora(infoDevice):
    conn = reintentar_conexion(infoDevice)
    actualizar_hora_conexion(infoDevice, conn)
    return

def actualizar_hora_conexion(infoDevice, conn):
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

def obtener_cantidad_marcaciones():
    # Obtiene la ubicación del archivo de texto
    filePath = os.path.join(os.path.abspath('.'), 'info_devices.txt')
    logging.debug(filePath)
    infoDevices = None
    try:
        # Obtiene todos los dispositivos en una lista formateada
        infoDevices = obtener_info_dispositivos(filePath)
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
                    conn.get_attendance()
                    cantidad_marcaciones[infoDevice["ip"]] = conn.records
                else:
                    cantidad_marcaciones[infoDevice["ip"]] = 'Falló'
                
    return cantidad_marcaciones