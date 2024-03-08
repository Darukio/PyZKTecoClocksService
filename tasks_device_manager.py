from connection import *
from file_manager import *
from datetime import datetime
from errors import ConexionFallida
from utils import logging
import os

def gestionar_marcaciones_dispositivos():
    # Lee las IPs desde el archivo de texto
    filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'file_ips.txt')
    ips = cargar_desde_archivo(filePath)
        
    # Itera a través de las IPs
    for ipDevice in ips:
        conn = None
        try:
            conn = conectar(ipDevice, port=4370)
        except ConexionFallida as e:
            logging.error(e)

        if conn:
            logging.info(f'Processing IP: {ipDevice}')
            actualizar_hora(conn)
            gestionar_marcaciones_individual(ipDevice, conn)
            gestionar_marcaciones_global(conn)
            finalizar_conexion(conn)

def gestionar_marcaciones_individual(ipDevice, conn):
    folderPath = crear_carpeta_y_devolver_ruta(ipDevice)
    newtime = datetime.today().date()
    dateString = newtime.strftime("%Y-%m-%d")
    fileName = ipDevice+'_'+dateString+'_file.cro'
    gestionar_guardado_de_marcaciones(conn, folderPath, fileName)

def gestionar_marcaciones_global(conn):
    folderPath = os.path.dirname(os.path.abspath(__file__))
    fileName = 'attendances_file.txt'
    gestionar_guardado_de_marcaciones(conn, folderPath, fileName)

def gestionar_guardado_de_marcaciones(conn, folderPath, fileName):
    destinyPath = os.path.join(folderPath, fileName)
    attendances = obtener_marcaciones(conn)
    logging.info('Attendances: ', attendances)
    logging.debug('DestinyPath: ', destinyPath)
    guardar_marcaciones_en_archivo(attendances, destinyPath)

def actualizar_hora_dispositivos():
    # Lee las IPs desde el archivo de texto
    filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'file_ips.txt')
    ips = cargar_desde_archivo(filePath)
        
    # Itera a través de las IPs
    for ipDevice in ips:
        conn = None
        try:
            conn = conectar(ipDevice, port=4370)
        except ConexionFallida as e:
            logging.error(e)

        if conn:
            logging.info(f'Processing IP: {ipDevice}')
            actualizar_hora(conn)
            finalizar_conexion(conn)