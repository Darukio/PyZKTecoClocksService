from zk import ZK
from datetime import datetime
from errors import ConexionFallida
from utils import logging

def conectar(ip, port):
    try:
        zk = ZK(ip, port, timeout=5)
        conn = None
        logging.info(f'Connecting to device {ip}...')
        conn = zk.connect()
        logging.info('Disabling device...')
        conn.disable_device()
        conn.test_voice(index=10)
    except ConexionFallida as e:
        raise e(ip)
    finally:
        return conn

def finalizar_conexion(conn):
    logging.info('Enabling device...')
    conn.enable_device()
    logging.info('Disconnecting device...')
    conn.disconnect()
    
def actualizar_hora(conn):
    # get current machine's time
    zktime = conn.get_time()
    print(zktime)
    # update new time to machine
    newtime = datetime.today()
    conn.set_time(newtime)

def obtener_marcaciones(conn):
    attendances = []
    try:
        logging.info('Getting attendances...')
        attendances = conn.get_attendance()
        conn.clear_attendance()
    except Exception as e:
        logging.error(f'Process terminate: {e}')
    finally:
        return attendances