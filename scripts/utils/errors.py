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

class ErrorConEscrituraEnArchivo(Exception):
    def __init__(self, nombre_modelo, punto_marcacion, ip, message_prefix):
        try:
            from .file_manager import crear_carpeta_y_devolver_ruta
            # Llama a la función desde el módulo importado
            folder_path = crear_carpeta_y_devolver_ruta('devices', 'errors')
            new_date = datetime.today().date().strftime("%Y-%m-%d")
            file_name = f'errors_{new_date}.txt'
            file_path = os.path.join(folder_path, file_name)
            current_time = datetime.now().strftime("%H:%M:%S")
            self.mensaje = f'{current_time} {message_prefix} {nombre_modelo} - {punto_marcacion}: {ip}\n'
            with open(file_path, 'a') as file:
                file.write(self.mensaje)
            self.mensaje = f'{message_prefix} {nombre_modelo} - {punto_marcacion}: {ip}'
            super().__init__(self.mensaje)
        except Exception as e:
            logging.error(f'Error al manejar excepción: {e}')

class IntentoConexionFallida(Exception):
    pass

class ConexionFallida(ErrorConEscrituraEnArchivo):
    def __init__(self, nombre_modelo, punto_marcacion, ip):
        message_prefix = 'Conexion fallida con'
        super().__init__(nombre_modelo, punto_marcacion, ip, message_prefix)

class HoraValidacionFallida(Exception):
    def __init__(self):
        self.mensaje = 'Hours or date between device and machine doesn\'t match'
        super().__init__(self.mensaje)

class HoraDesactualizada(ErrorConEscrituraEnArchivo):
    def __init__(self, nombre_modelo, punto_marcacion, ip):
        message_prefix = 'Pila fallando de'
        super().__init__(nombre_modelo, punto_marcacion, ip, message_prefix)

class CargaArchivoFallida(Exception):
    def __init__(self, file_path):
        self.mensaje = f'Carga fallida del archivo {file_path}'
        super().__init__(self.mensaje)