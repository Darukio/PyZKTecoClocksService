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

class ConexionFallida(Exception):
    def __init__(self, nombreModelo, puntoMarcacion, ip):
        super().__init__()
        try:
            from file_manager import crear_carpeta_y_devolver_ruta
            # Call the function from the imported module
            folderPath = crear_carpeta_y_devolver_ruta('devices', 'errors')
            newtime = datetime.today().date()
            dateString = newtime.strftime("%Y-%m-%d")
            logging.debug(dateString)
            fileName = f'errors_{dateString}.txt'
            logging.debug(fileName)
            filePath = os.path.join(folderPath, fileName)
            hourString = datetime.now().strftime("%H:%M:%S")
            self.mensaje = f'{hourString} Conexion fallida con {nombreModelo} - {puntoMarcacion}: {ip}\n' 
            with open(filePath, 'a') as file:
                file.write(self.mensaje)
        except Exception as e:
            logging.error(e)

class HoraDesactualizada(Exception):
    def __init__(self, nombreModelo, puntoMarcacion, ip):
        super().__init__()
        try:
            from file_manager import crear_carpeta_y_devolver_ruta
            # Call the function from the imported module
            folderPath = crear_carpeta_y_devolver_ruta('devices', 'errors')
            newtime = datetime.today().date()
            dateString = newtime.strftime("%Y-%m-%d")
            logging.debug(dateString)
            fileName = f'errors_{dateString}.txt'
            logging.debug(fileName)
            filePath = os.path.join(folderPath, fileName)
            hourString = datetime.now().strftime("%H:%M:%S")
            self.mensaje = f'{hourString} Pila fallando de {nombreModelo} - {puntoMarcacion}: {ip}\n' 
            with open(filePath, 'a') as file:
                file.write(self.mensaje)
        except Exception as e:
            logging.error(e)
    
class CargaArchivoFallida(Exception):
    def __init__(self, filePath):
        self.mensaje = f'Carga fallida del archivo {filePath}: {str(Exception)}' 
        super().__init__(self.mensaje)