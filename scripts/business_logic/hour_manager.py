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
from .connection import *
from .device_manager import *

def actualizar_hora_dispositivos(desde_thread = False):
    info_devices = []
    try:
        # Obtiene todos los dispositivos en una lista formateada
        info_devices = obtener_info_dispositivos()
    except Exception as e:
        logging.error(e)

    if info_devices:
        gt = []
        config.read(os.path.join(encontrar_directorio_raiz(), 'config.ini'))
        coroutines_pool_max_size = int(config['Cpu_config']['coroutines_pool_max_size'])
        # Crea un pool de green threads
        pool = eventlet.GreenPool(coroutines_pool_max_size)
        
        for info_device in info_devices:
            # Si el dispositivo se encuentra activo...
            if eval(info_device["activo"]) or desde_thread:
                logging.debug(info_device)
                # Lanza una corutina para cada dispositivo activo
                try:
                    gt.append(pool.spawn(actualizar_hora_dispositivo, info_device))
                except Exception as e:
                    pass
        
        # Espera a que todas las corutinas en el pool hayan terminado
        for g in gt:
            try:
                g.wait()
            except Exception as e:
                logging.error(e)

        print('TERMINE HORA!')
        logging.debug('TERMINE HORA!')

def actualizar_hora_dispositivo(info_device):
    try:
        reintentar_operacion_de_red(actualizar_hora, args=(info_device['ip'], 4370, info_device['communication'],))
    except IntentoConexionFallida as e:
        raise ConexionFallida(info_device['nombre_modelo'], info_device['punto_marcacion'], info_device['ip'])
    except HoraValidacionFallida as e:
        raise HoraDesactualizada(info_device["nombre_modelo"], info_device["punto_marcacion"], info_device["ip"])
    except Exception as e:
        raise e
