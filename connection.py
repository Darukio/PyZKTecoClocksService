from zk import ZK
from datetime import datetime
import os
logPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'service_log.txt')

def conectar(ip, port):
    zk = ZK(ip, port, timeout=5)
    try:
        print('Connecting to device...')
        conn = zk.connect()
        print('Disabling device...')
        conn.disable_device()
        conn.test_voice(index=10)
    except Exception as e:
        raise e
    finally:
        return conn
    
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
        print('Getting attendances...')
        attendances = conn.get_attendance()
        conn.clear_attendance()
    except Exception as e:
        print(f'Process terminate: ', e)
    finally:
        return attendances