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

from datetime import datetime
import os
import logging
import sys
from .file_manager import *
import locale

locale.setlocale(locale.LC_TIME, "Spanish_Argentina.1252")  # Español de Argentina

def config_log():
    logs_folder = os.path.join(encontrar_directorio_raiz(), 'logs')

    # Crear la carpeta logs si no existe
    if not os.path.exists(logs_folder):
        os.makedirs(logs_folder)

    new_time = datetime.today().date()
    date_string = new_time.strftime("%Y-%b")
    logs_month_folder = os.path.join(logs_folder, date_string)

    # Crear la carpeta logs_month si no existe
    if not os.path.exists(logs_month_folder):
        os.makedirs(logs_month_folder)

    debug_log_file = os.path.join(logs_month_folder, 'program_debug.log')

    # Configurar el sistema de registros básico para program_debug.log
    logging.basicConfig(
        filename=debug_log_file,
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s'
    )

    # Configurar un controlador adicional para 'program_error.log'
    error_log_file = os.path.join(logs_month_folder, 'program_error.log')
    error_logger = logging.FileHandler(error_log_file)
    error_logger.setLevel(logging.WARNING)

    # Definir un formato para el controlador adicional
    error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    error_logger.setFormatter(error_formatter)

    # Agregar el controlador adicional al sistema de registros
    logging.getLogger().addHandler(error_logger)

# Ejemplos de registros
# logging.debug('Este es un mensaje de depuración')
# logging.info('Este es un mensaje informativo')
# logging.warning('Este es un mensaje de advertencia')
# logging.error('Este es un mensaje de error')
# logging.critical('Este es un mensaje crítico')
'''
Los niveles son jerarquicos. Si se establece en debug, 
se podran ver los mensajes de debug hasta critical. 
Si se establece en critical, se podran ver solamente 
los mensajes critical
'''