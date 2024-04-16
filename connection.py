from zk import ZK
from datetime import datetime
from utils import logging
import threading

def conectar(ip, port):
    conn = None
    try:
        zk = ZK(ip, port, timeout=5)
        logging.info(f'Connecting to device {ip}...')
        conn = zk.connect()
    except Exception as e:
        logging.warning(e)
        # Si falla la conexión, iniciar un hilo aparte para intentar nuevamente
        thread = threading.Thread(target=reintentar_conexion, args=(ip, port))
        thread.start()
        pass
    finally:
        if conn is not None:
            #logging.info('Disabling device...')
            #conn.disable_device()
            logging.info(f'Successfully connected to device {ip}.')
            conn.test_voice(index=10)
        return conn

def reintentar_conexion(ip, port):
    logging.info(f'Retrying connection to device {ip}...')
    intentos_maximos = 3
    intentos = 0
    while intentos < intentos_maximos:  # Intenta conectar hasta 3 veces
        try:
            zk = ZK(ip, port, timeout=5)
            logging.info(f'Successfully connected to device {ip}.')
            conn = zk.connect()
            conn.test_voice(index=10)
            return conn
        except Exception as e:
            logging.warning(f'Failed to connect to device {ip}. Retrying...')
            intentos += 1
    logging.error(f'Unable to connect to device {ip} after {intentos} attempts.')
    raise Exception

def finalizar_conexion(conn):
    #logging.info('Enabling device...')
    #conn.enable_device()
    logging.info('Disconnecting device...')
    conn.disconnect()
    
def actualizar_hora(conn):
    # get current machine's time
    try:
        validar_hora(conn.get_time())
    except Exception as e:
        raise Exception(e)
    # update new time to machine
    newtime = datetime.today()
    conn.set_time(newtime)

def validar_hora(zktime):
    newtime = datetime.today()
    logging.debug(f'Hour device: {zktime.hour}:{zktime.min} - Hour machine: {newtime.hour}:{newtime.min}')
    if zktime.hour != newtime.hour or zktime.min != newtime.min:
        raise Exception('Hours between device and machine doesn\'t match')
    
def obtener_marcaciones(conn, intentos=0):
    attendances = []
    try:
        logging.info('Getting attendances...')
        attendances = conn.get_attendance()
        #conn.clear_attendance()
        logging.debug(f'Length of attendances from device: {conn.records}, Length of attendances: {len(attendances)}')
        if conn.records != len(attendances):
            if intentos < 3:
                logging.warning(f"Records mismatch. Retrying... Attempt {intentos+1}")
                return obtener_marcaciones(conn, intentos + 1)
            else:
                logging.error("Failed to retrieve attendances after 3 attempts.")
    except Exception as e:
        logging.error(f'Process terminated: {e}')
    finally:
        return attendances