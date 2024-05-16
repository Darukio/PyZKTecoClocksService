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
    try:    
        raise ConexionFallida(infoDevice['nombreModelo'], infoDevice['puntoMarcacion'], infoDevice['ip'])
    except ConexionFallida:
        pass