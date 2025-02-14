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

import logging
import os
from datetime import datetime
import eventlet
from zk import ZK, ZK_helper
from scripts import config
from scripts.utils.errors import OutdatedTimeError
from scripts.utils.file_manager import find_root_directory

def connect(ip, port, communication):
    conn = None
    try:
        p_force_udp = True if communication == 'UDP' else False
        zk = ZK(ip, port, ommit_ping=True, force_udp=p_force_udp)
        logging.info(f'Conectando al dispositivo {ip}...')
        conn = zk.connect()
        logging.info(f'Conectado exitosamente al dispositivo {ip}')
        logging.debug(f'{ip}: {conn}')
        try:
            logging.info(f'{ip} - Platform: {conn.get_platform()}')
            logging.info(f'{ip} - Device name: {conn.get_device_name()}')
            logging.info(f'{ip} - Firmware version: {conn.get_firmware_version()}')
            logging.info(f'{ip} - Old firmware: {conn.get_compat_old_firmware()}')
        except Exception as e:
            pass
    except Exception as e:
        raise ConnectionRefusedError from e
    eventlet.sleep(0)
    return conn

def ping_device(ip, port):
    try:
        config.read(os.path.join(find_root_directory(), 'config.ini'))
        zk_helper = ZK_helper(ip, port, config['Network_config']['size_ping_test_connection'])
        return zk_helper.test_ping()
    except Exception as e:
        raise ConnectionRefusedError from e
    
def end_connection(conn, ip):
    try:
        logging.info(f'Desconectando dispositivo {ip}...')
        conn.disconnect()
    except Exception as e:
        logging.warning(e)
        raise ConnectionRefusedError from e
    eventlet.sleep(0)
    
def update_time(conn, from_service=False):
    ip = None
    try:
        ip = conn.get_network_params()["ip"]
        zktime = conn.get_time()
        logging.debug(f'{ip} - Dispositivo: {zktime} - Maquina local: {datetime.today()}')
        eventlet.sleep(0)
    except Exception as e:
        raise ConnectionRefusedError from e

    try:
        logging.debug(f'Actualizando hora del dispositivo {ip}...')
        newtime = datetime.today()
        conn.set_time(newtime)
        eventlet.sleep(0)
    except Exception as e:
        raise ConnectionRefusedError from e

    try:
        logging.debug(f'Validando hora del dispositivo {ip}...')
        validate_time(zktime)
        eventlet.sleep(0)
    except OutdatedTimeError as e:
        raise OutdatedTimeError(ip) from e

    return

def validate_time(zktime):
    newtime = datetime.today()
    if (abs(zktime.hour - newtime.hour) > 0 or
    abs(zktime.minute - newtime.minute) >= 5 or
    zktime.day != newtime.day or
    zktime.month != newtime.month or
    zktime.year != newtime.year):
        raise OutdatedTimeError()
    
def get_attendances(conn, from_service):
    attendances = []
    ip = None
    try:
        ip = conn.get_network_params()["ip"]
    except Exception as e:
        logging.error(e)

    try:
        logging.info(f'Obteniendo marcaciones del dispositivo {ip}...')
        import time
        start_time = time.time()
        attendances = conn.get_attendance()
        end_time = time.time()
        logging.debug(f'{ip} - Ending attendances operation - Time operation: {end_time - start_time} - Time ending: {end_time}')
        records = conn.records
        logging.debug(f'{ip} - Length of attendances from device: {records}, Length of attendances: {len(attendances)}')
        if records != len(attendances):
            raise Exception('Records mismatch')
        else:
            conn.get_attendance()
            new_records = conn.records
            logging.debug(f'{ip} - Length of attendances last conn: {new_records}, Length of attendances old conn: {records}')
            if new_records != records:
                raise Exception('Records mismatch')

            start_time_2 = time.time()
            config.read(os.path.join(find_root_directory(), 'config.ini'))
            # Determine the appropriate configuration based on the value of from_service
            config_key = 'clear_attendance_service' if from_service else 'clear_attendance'
            logging.debug(f'clear_attendance: {config['Device_config'][config_key]}')

            # Evaluate the selected configuration
            if eval(config['Device_config'][config_key]):
                logging.debug(f'{ip} - Clearing attendances...')
                try:
                    end_time_2 = time.time()
                    logging.debug(f'{ip} - Ending clear attendances operation - Time operation: {end_time_2 - start_time_2} - Time ending: {end_time_2}')
                    conn.clear_attendance()
                    eventlet.sleep(0)
                except Exception as e:
                    logging.error(f'{ip} - Can\'t clear attendances')
                    raise e

            return attendances
    except Exception as e:
        raise ConnectionRefusedError from e

def get_attendance_count(conn, from_service=None):
    ip = None
    try:
        ip = conn.get_network_params()["ip"]
    except Exception as e:
        logging.error(e)
        
    try:
        atte = conn.get_attendance()
        logging.debug(atte)
        records = conn.records
        logging.debug(records)
        eventlet.sleep(0)
        return records
    except Exception as e:
        raise ConnectionRefusedError from e

def restart_device(conn, from_service=None):
    ip = None
    try:
        ip = conn.get_network_params()["ip"]
    except Exception as e:
        logging.error(e)

    try:
        logging.info(f"Reiniciando dispositivo {ip}...")
        conn.restart()
        return
    except Exception as e:
        raise ConnectionRefusedError from e