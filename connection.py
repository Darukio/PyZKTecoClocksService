"""
    PyZKTecoClocks: GUI for managing ZKTeco clocks, enabling clock 
    time synchronization and attendance data retrieval.
    Copyright (C) 2024  Paulo Sebastian Spaciuk (Darukio)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from zk import ZK
from datetime import datetime
from utils import logging
import configparser

# Para leer un archivo INI
config = configparser.ConfigParser()

def conectar(ip, port):
    conn = None
    try:
        zk = ZK(ip, port, timeout=60)
        logging.info(f'Connecting to device {ip}...')
        conn = zk.connect()
    except Exception as e:
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
    try:
        logging.info(f'{conn.get_network_params()['ip']} - Disconnecting device...')
        conn.disconnect()
    except Exception as e:
        raise Exception(str(e))
    
def actualizar_hora(conn):
    # get current machine's time
    try:
        zktime = conn.get_time()
        logging.debug(f'{conn.get_network_params()['ip']} - Date and hour device: {zktime} - Date and hour machine: {newtime}')
        validar_hora(zktime)
    except Exception as e:
        raise Exception(str(e))
    finally:
        # update new time to machine
        newtime = datetime.today()
        conn.set_time(newtime)

def validar_hora(zktime):
    newtime = datetime.today()
    if (abs(zktime.hour - newtime.hour) > 0 or
    abs(zktime.minute - newtime.minute) >= 5 or
    zktime.day != newtime.day or
    zktime.month != newtime.month or
    zktime.year != newtime.year):
        raise Exception('Hours or date between device and machine doesn\'t match')
    
def obtener_marcaciones(conn, intentos=0):
    attendances = []
    try:
        logging.info(f'{conn.get_network_params()['ip']} - Getting attendances...')
        attendances = conn.get_attendance()
        if conn.records != len(attendances):
            if intentos < 3:
                logging.warning(f"{conn.get_network_params()['ip']} - Records mismatch. Retrying... Attempt {intentos+1}")
                return obtener_marcaciones(conn, intentos + 1)
            else:
                logging.error(f"{conn.get_network_params()['ip']} - Failed to retrieve attendances after 3 attempts.")
        else:
            config.read('config.ini')
            logging.debug(f'clear_attendance: {config['Device_config']['clear_attendance']}')
            if eval(config['Device_config']['clear_attendance']):
                logging.debug(f'{conn.get_network_params()['ip']} - Clearing attendances...')
                conn.clear_attendance()
            logging.debug(f'{conn.get_network_params()['ip']} - Length of attendances from device: {conn.records}, Length of attendances: {len(attendances)}')
    except Exception as e:
        logging.error(f'Process terminated: {e}')
    return attendances