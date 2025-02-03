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
from scripts import config
from scripts.business_logic.connection import get_attendance_count, get_attendances
from scripts.business_logic.device_manager import get_device_info, retry_network_operation
from scripts.utils.errors import ConnectionFailedError, NetworkError
from scripts.utils.file_manager import create_folder_and_return_path, find_root_directory, save_attendances_to_file
from .hour_manager import update_device_time_single
from datetime import datetime
import os
import threading
import eventlet
from eventlet.green import threading

class SharedState:
    def __init__(self):
        self.total_devices = 0
        self.processed_devices = 0
        self.lock = threading.Lock()

    def increment_processed_devices(self):
        with self.lock:
            self.processed_devices += 1
            return self.processed_devices

    def calculate_progress(self):
        with self.lock:
            if self.total_devices > 0:
                return int((self.processed_devices / self.total_devices) * 100)
            return 0

    def set_total_devices(self, total):
        with self.lock:
            self.total_devices = total

    def get_total_devices(self):
        return self.total_devices

def manage_device_attendances(from_service=False, emit_progress=None):
    logging.debug(f'desde_service = {from_service}')
    device_info = []
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
        state = SharedState()

        for info in device_info:
            logging.debug(f'info_device["active"]: {eval(info["active"])} - from_service: {from_service}')
            if eval(info["active"]) or from_service:
                logging.debug(f'info_device_active: {info}')
                active_devices.append(info)

        # Set the total number of devices in the shared state
        state.set_total_devices(len(active_devices))
                
        for active_device in active_devices:
            try:
                gt.append(pool.spawn(manage_device_attendance_single, active_device, from_service, emit_progress, state))
            except Exception as e:
                pass
        
        for active_device, g in zip(active_devices, gt):
            logging.debug(f'Processing {active_device}')
            try:
                logging.debug(g)
                attendance_count = g.wait()
            except Exception as e:
                logging.error(e)
                attendance_count = 'Conexión fallida'

            # Save the information in results
            results[active_device["ip"]] = {
                "point": active_device["point"],
                "district_name": active_device["district_name"],
                "id": active_device["id"],
                "attendance_count": str(attendance_count)
            }
            logging.debug(results[active_device["ip"]])

        print('TERMINE MARCACIONES!')
        logging.debug('TERMINE MARCACIONES!')

    return results

def manage_device_attendance_single(info, from_service, emit_progress, state):
    try:
        try:
            attendances = retry_network_operation(get_attendances, args=(info['ip'], 4370, info['communication'],), from_service=from_service)
            attendances = format_attendances(attendances, info["id"])
            logging.info(f'{info["ip"]} - Length attendances: {len(attendances)} - Attendances: {attendances}')
            
            manage_individual_attendances(info, attendances)
            manage_global_attendances(attendances)
        except ConnectionFailedError as e:
            raise NetworkError(info['model_name'], info['point'], info['ip'])
        except Exception as e:
            raise e

        try:
            update_device_time_single(info)
        except Exception as e:
            logging.error(e)

        logging.debug(f'TERMINANDO MARCACIONES DISP {info["ip"]}')
        return len(attendances)
    except Exception as e:
        raise e
    finally:
        try:
            # Update the number of processed devices and progress
            processed_devices = state.increment_processed_devices()
            if emit_progress:
                progress = state.calculate_progress()
                emit_progress(percent_progress=progress, device_progress=info["ip"], processed_devices=processed_devices, total_devices=state.get_total_devices())
                logging.debug(f"processed_devices: {processed_devices}/{state.get_total_devices()}, progress: {progress}%")
        except Exception as e:
            logging.error(e)

# Define the transformation mapping
config.read(os.path.join(find_root_directory(), 'config.ini'))
attendance_status_dictionary = {
    1: config['Attendance_status']['status_fingerprint'],
    15: config['Attendance_status']['status_face'],
    0: config['Attendance_status']['status_card'],
    2: config['Attendance_status']['status_card'],
    4: config['Attendance_status']['status_card'],
}

# Function that applies the transformation according to the dictionary
def maping_dictionary(number):
    # If the number is in the dictionary, return the transformed value
    if number in attendance_status_dictionary:
        return attendance_status_dictionary[number]
    # Optional: Handle unspecified cases
    else:
        return 0

def format_attendances(attendances, id):
    formatted_attendances = []
    for attendance in attendances:
        formatted_timestamp = attendance.timestamp.strftime("%d/%m/%Y %H:%M") # Format the timestamp to DD/MM/YYYY hh:mm, example: 21/07/2023 05:28
        attendance_formatted = {
            "user_id": str(attendance.user_id).zfill(9),
            "timestamp": formatted_timestamp,
            "id": id,
            "status": maping_dictionary(int(attendance.status)),
        }
        formatted_attendances.append(attendance_formatted)
    return formatted_attendances

def manage_individual_attendances(info, attendances):
    folder_path = create_folder_and_return_path('devices', info["district_name"], info["model_name"] + "-" + info["point"])
    new_time = datetime.today().date()
    date_string = new_time.strftime("%Y-%m-%d")
    file_name = info["ip"]+'_'+date_string+'_file.cro'
    manage_attendance_saving(attendances, folder_path, file_name)

def manage_global_attendances(attendances):
    # Get the value of name_attendances_file from the [Program_config] section
    config.read(os.path.join(find_root_directory(), 'config.ini'))
    name_attendances_file = config['Program_config']['name_attendances_file']
    folder_path = find_root_directory()
    file_name = f"{name_attendances_file}.txt"
    manage_attendance_saving(attendances, folder_path, file_name)

def manage_attendance_saving(attendances, folder_path, file_name):
    destiny_path = os.path.join(folder_path, file_name)
    logging.debug(f'destiny_path: {destiny_path}')
    save_attendances_to_file(attendances, destiny_path)

def get_device_attendance_count(emit_progress=None):
    device_info = []
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
                    gt.append(pool.spawn(get_device_attendance_count_single, info))
                except Exception as e:
                    pass
                active_devices.append(info)

        for active_device, g in zip(active_devices, gt): 
            try:
                attendance_count = g.wait()
            except Exception as e:
                logging.error(e)
                attendance_count = 'Conexión fallida'
                    
            # Save the information in results
            results[active_device["ip"]] = {
                "point": active_device["point"],
                "district_name": active_device["district_name"],
                "id": active_device["id"],
                "attendance_count": str(attendance_count)
            }
            logging.debug(results[active_device["ip"]])

        #failed_connections = {ip: info for ip, info in results.items() if info["status"] == "Conexión fallida"}
        print('TERMINE CANT MARCACIONES!')
        logging.debug('TERMINE CANT MARCACIONES!')

    return results

def get_device_attendance_count_single(info):
    try:
        records = retry_network_operation(get_attendance_count, args=(info["ip"], 4370, info['communication'],))
        logging.debug(f'IP: {info["ip"]} - Records: {records}')
        return records
    except ConnectionFailedError as e:
        raise NetworkError(info['model_name'], info['point'], info['ip'])
    except Exception as e:
        raise e

    return