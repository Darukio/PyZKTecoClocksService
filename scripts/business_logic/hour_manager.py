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
from scripts.business_logic.device_manager import get_device_info, retry_network_operation
from scripts.utils.errors import BatteryFailingError, ConnectionFailedError, NetworkError
from .connection import *

def update_device_time(from_service=False, emit_progress=None):
    device_info = []
    try:
        # Get all devices in a formatted list
        device_info = get_device_info()
    except Exception as e:
        logging.error(e)

    if device_info:
        gt = []
        config.read(os.path.join(find_root_directory(), 'config.ini'))
        coroutines_pool_max_size = int(config['Cpu_config']['coroutines_pool_max_size'])
        # Create a pool of green threads
        pool = eventlet.GreenPool(coroutines_pool_max_size)
        
        for info in device_info:
            # If the device is active...
            if eval(info["active"]) or from_service:
                logging.debug(info)
                # Launch a coroutine for each active device
                try:
                    gt.append(pool.spawn(update_device_time_single, info))
                except Exception as e:
                    pass
        
        # Wait for all coroutines in the pool to finish
        for g in gt:
            try:
                g.wait()
            except Exception as e:
                logging.error(e)

        print('TERMINE HORA!')
        logging.debug('TERMINE HORA!')

def update_device_time_single(info):
    try:
        retry_network_operation(update_time, args=(info['ip'], 4370, info['communication'],))
    except ConnectionFailedError as e:
        raise NetworkError(info['model_name'], info['point'], info['ip'])
    except OutdatedTimeError as e:
        raise BatteryFailingError(info["model_name"], info["point"], info["ip"])
    except Exception as e:
        raise e
