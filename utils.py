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

# Configurar el sistema de registros básico para program_debug.log
logging.basicConfig(filename='program_debug.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Configurar un controlador adicional para los niveles de warning, error y critical en program_error.log
error_logger = logging.FileHandler('program_error.log')
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