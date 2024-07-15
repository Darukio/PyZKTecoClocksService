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

from ..utils.errors import *
from ..utils.file_manager import *
import logging
import eventlet
import os
from scripts import config
from datetime import datetime
from zk import ZK, ZK_helper
from scripts import config

def conectar(ip, port, ommit_ping=True):
    conn = None
    try:
        zk = ZK(ip, port)
        logging.info(f'Connecting to device {ip}...')
        conn = zk.connect()
        logging.debug(conn)
        logging.debug(conn.get_platform())
        logging.debug(conn.get_device_name())
        #logging.info('Disabling device...')
        #conn.disable_device()
        logging.info(f'Successfully connected to device {ip}.')
        #conn.test_voice(index=10)
    except Exception as e:
        raise IntentoConexionFallida from e
    eventlet.sleep(0)
    return conn

def ping_device(ip, port):
    try:
        config.read('config.ini')
        zk_helper = ZK_helper(ip, port, config['Network_config']['size_ping_test_connection'])
        return zk_helper.test_ping()
    except Exception as e:
        logging.error(e)
        return False
    
def finalizar_conexion(conn):
    #logging.info('Enabling device...')
    #conn.enable_device()
    try:
        logging.info(f'{conn.get_network_params()["ip"]} - Disconnecting device...')
        conn.disconnect()
    except Exception as e:
        raise e
    eventlet.sleep(0)
    
def actualizar_hora(conn):
    ip = None
    try:
        ip = conn.get_network_params()["ip"]
        zktime = conn.get_time()
        logging.debug(f'{ip} - Date and hour device: {zktime} - Date and hour machine: {datetime.today()}')
        eventlet.sleep(0)
    except Exception as e:
        raise IntentoConexionFallida from e

    try:
        logging.debug(f'{ip} - Setting updated hour...')
        newtime = datetime.today()
        conn.set_time(newtime)
        eventlet.sleep(0)
    except Exception as e:
        raise IntentoConexionFallida from e

    try:
        logging.debug(f'{ip} - Validating hour device...')
        validar_hora(zktime)
        eventlet.sleep(0)
    except Exception as e:
        raise HoraValidacionFallida from e

    return

def validar_hora(zktime):
    newtime = datetime.today()
    if (abs(zktime.hour - newtime.hour) > 0 or
    abs(zktime.minute - newtime.minute) >= 5 or
    zktime.day != newtime.day or
    zktime.month != newtime.month or
    zktime.year != newtime.year):
        raise Exception('Hours or date between device and machine doesn\'t match')
    
def obtener_marcaciones(conn):
    attendances = []
    try:
        ip = conn.get_network_params()["ip"]
        logging.info(f'{ip} - Getting attendances...')
        attendances = conn.get_attendance()
        records = conn.records
        eventlet.sleep(0)
        logging.debug(f'{ip} - Length of attendances from device: {records}, Length of attendances: {len(attendances)}')
        if records != len(attendances):
            raise Exception('Records mismatch')
        else:
            config.read('config.ini')
            logging.debug(f'clear_attendance: {config['Device_config']['clear_attendance']}')
            if eval(config['Device_config']['clear_attendance']):
                logging.debug(f'{ip} - Clearing attendances...')
                try:
                    conn.clear_attendance()
                    eventlet.sleep(0)
                except Exception as e:
                    logging.error(f'{ip} - Can\'t clear attendances')
                    raise e
            return attendances
    except Exception as e:
        raise IntentoConexionFallida from e

def obtener_cantidad_marcaciones(conn):
    try:
        conn.get_attendance()
        records = conn.records
        eventlet.sleep(0)
        return records
    except Exception as e:
        raise IntentoConexionFallida from e