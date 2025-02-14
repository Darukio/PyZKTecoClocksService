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
import eventlet
import os
from scripts import config
from scripts import config
from scripts.business_logic.connection import connect, end_connection, ping_device
from scripts.utils.errors import ConnectionFailedError, OutdatedTimeError
from scripts.utils.file_manager import find_root_directory, load_from_file

def organize_device_info(line):
    # Split the line into parts using the separator " - "
    parts = line.strip().split(" - ")
    # Check that there are exactly 7 parts in the line
    if len(parts) == 8:
        # Return an object with attributes
        return {
            "district_name": parts[0],
            "model_name": parts[1],
            "point": parts[2],
            "ip": parts[3],
            "id": parts[4],
            "communication": parts[5],
            "battery": parts[6],
            "active": parts[7]
        }
    else:
        # If there are not exactly 8 parts, return None
        return None

def get_device_info():
    # Get the location of the text file
    file_path = os.path.join(find_root_directory(), 'info_devices.txt')
    # Get the device info from info_devices.txt
    data_list = load_from_file(file_path)
    device_info = []
    # Iterate over the different devices
    for data in data_list:
        # Create a device object from the unformatted line
        line = organize_device_info(data)
        if line:
            # Append the device to the device list
            device_info.append(line)
    return device_info

def ping_devices(emit_progress=None):
    device_info = None
    try:
        # Get all devices in a formatted list
        device_info = get_device_info()
    except Exception as e:
        logging.error(e)

    results = {}

    if device_info:
        gt = []
        active_devices = []
        config.read(os.path.join(find_root_directory(), 'config.ini'))
        coroutines_pool_max_size = int(config['Cpu_config']['coroutines_pool_max_size'])
        
        # Create a pool of green threads
        pool = eventlet.GreenPool(coroutines_pool_max_size)
        for info in device_info:
            if eval(info["active"]):
                try:
                    gt.append(pool.spawn(ping_device, info["ip"], 4370))
                except Exception as e:
                    pass
                active_devices.append(info)

        for active_device, g in zip(active_devices, gt):
            response = g.wait()
            if response:
                status = "Conexión exitosa"
            else:
                status = "Conexión fallida"

            # Save the information in results
            results[active_device["ip"]] = {
                "point": active_device["point"],
                "district_name": active_device["district_name"],
                "id": active_device["id"],
                "status": status
            }

        print('TERMINE PING!')
        logging.debug('TERMINE PING!')

    return results

def update_device_name(conn, ip):
    try:
        device_name = conn.get_device_name()
        device_name = device_name.replace(" ", "")
        if not device_name:
            try:
                serial_number = conn.get_serialnumber()
                device_name = serial_number
                if serial_number == "52355702520030":
                    device_name = "MultiBio700/ID"
            except Exception as e:
                logging.error(f"Error al obtener el nombre del dispositivo {ip}: {e}")
                device_name = "NoName"
        try:
            with open('info_devices.txt', 'r') as file:
                lines = file.readlines()

            new_lines = []
            for line in lines:
                parts = line.strip().split(' - ')

                if parts[3] == ip and parts[1] != device_name:
                    logging.debug(f'Reemplazando nombre del dispositivo {ip}... {parts[1]} por {device_name}')
                    parts[1] = device_name
                new_lines.append(' - '.join(parts) + '\n')

            with open('info_devices.txt', 'w') as file:
                file.writelines(new_lines)
        except Exception as e:
            logging.error(f"Error al reemplazar el nombre del dispositivo: {e}")
    except Exception as e:
        pass

def retry_network_operation(op, args=(), kwargs={}, max_attempts=3, from_service=False):
    config.read(os.path.join(find_root_directory(), 'config.ini'))
    max_attempts = int(config['Network_config']['retry_connection'])
    result = None
    conn = None

    for _ in range(max_attempts):
        try:
            logging.debug(f'{args} CONECTANDO!')
            if conn is None:
                conn = connect(*args)
            if conn:
                logging.debug(f'{args} OPERACION DE RED!')
                if not from_service:
                    update_device_name(conn, args[0])
                result = op(conn, from_service)
                logging.debug(f'{args} FINALIZANDO!')
                end_connection(conn, args[0])
                logging.debug(f'{args} FINALIZADO!')
                break
        except OutdatedTimeError as e:
            logging.error("2: "+str(e))
            raise e
        except ConnectionRefusedError as e:
            conn = None
            if result:
                break
            error_message = f"Intento fallido {_ + 1} de {max_attempts} del dispositivo {args[0]} para la operacion {op.__name__}: {e.__cause__}"
            if _ + 1 == max_attempts:
                raise ConnectionFailedError(error_message) from e
            else:
                ConnectionFailedError(error_message)
            eventlet.sleep(0)
        except Exception as e:
            logging.error("3: "+str(e))
            pass
                
    logging.debug(f'{args} RESULTADO!')
    return result