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

import os
import threading
import logging
import sys

file_lock = threading.Lock()

def cargar_desde_archivo(file_path):
    '''
    Carga el contenido desde un archivo de texto.

    Parameters:
    - file_path (str): Ruta del archivo de texto.

    Returns:
    - List[str]: Lista del contenido del archivo.
    '''
    from .errors import CargaArchivoFallida

    content = []
    try:
        with open(file_path, 'r') as file:
            content = [line.strip() for line in file.readlines()] # Elimina los saltos de línea
    except CargaArchivoFallida as e:
        raise(e)
    return content

def crear_carpeta_y_devolver_ruta(*args):
    # Directorio base donde se almacenarán las carpetas con la IP
    ruta_destino = encontrar_directorio_raiz()
    
    for index, carpeta in enumerate(args, start=1):
        ruta_destino = os.path.join(ruta_destino, carpeta.lower())
        if not os.path.exists(ruta_destino):
            os.makedirs(ruta_destino)
            logging.debug(f'Se ha creado la carpeta {carpeta} en la ruta {ruta_destino}')
    
    return ruta_destino

def guardar_marcaciones_en_archivo(attendances, file):
    file_lock.acquire()
    try:
        with open(file, 'a') as f:
            for attendance in attendances:
                '''
                Dev:
                print('Attendance: ', attendance)
                print(dir(attendance))
                for attr_name, attr_value in vars(attendance).items():
                    print(f"{attr_name}: {type(attr_value)}")
                '''
                f.write(f"{attendance['user_id']} {attendance['timestamp']} {attendance['id']} {attendance['status']}\n")
    except Exception as e:
        logging.error(f'Process terminate: {e}')
    finally:
        file_lock.release()

def encontrar_directorio_de_marcador(marcador, path_actual=os.path.abspath(os.path.dirname(__file__))):
    while path_actual != os.path.dirname(path_actual):  # Mientras no se llegue al root del sistema de archivos
        logging.debug(f"Buscando en: {os.path.join(path_actual, marcador)}")
        if os.path.exists(os.path.join(path_actual, marcador)):
            return path_actual
        path_actual = os.path.dirname(path_actual)
    
    return None

def encontrar_directorio_raiz():
    path = None
    logging.debug(f'SE EJECUTA DESDE EXE?: {getattr(sys, 'frozen', False)}')
    if getattr(sys, 'frozen', False):
        path = os.path.dirname(sys.executable)
    else:
        marcador="main.py"
        logging.debug(path)
        path = encontrar_directorio_de_marcador(marcador)

    return path
