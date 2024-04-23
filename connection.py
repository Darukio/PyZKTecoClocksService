from zk import ZK
from datetime import datetime
from utils import logging

def conectar(ip, port):
    conn = None
    try:
        zk = ZK(ip, port, timeout=5)
        logging.info(f'Connecting to device {ip}...')
        conn = zk.connect()
    except Exception as e:
        # Si falla la conexión, iniciar un hilo aparte para intentar nuevamente
        raise Exception(str(e))
    if conn is not None:
        #logging.info('Disabling device...')
        #conn.disable_device()
        logging.info(f'Successfully connected to device {ip}.')
        conn.test_voice(index=10)
    return conn
    
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
        raise Exception(str(e))
    # update new time to machine
    newtime = datetime.today()
    conn.set_time(newtime)

def validar_hora(zktime):
    newtime = datetime.today()
    logging.info(f'Date and hour device: {zktime} - Date and hour machine: {newtime}')
    logging.debug(f'Device: {zktime.day}/{zktime.month}/{zktime.year} - Machine: {newtime.day}/{newtime.month}/{newtime.year}')
    if (abs(zktime.hour - newtime.hour) > 0 or
    abs(zktime.minute - newtime.minute) >= 5 or
    zktime.day != newtime.day or
    zktime.month != newtime.month or
    zktime.year != newtime.year):
        raise Exception('Hours or date between device and machine doesn\'t match')
    
def obtener_marcaciones(conn, intentos=0):
    attendances = []
    try:
        logging.info('Getting attendances...')
        attendances = conn.get_attendance()
        logging.info('Disabling device OFF')
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
    return attendances