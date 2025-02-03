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

def load_from_file(file_path):
    '''
    Load content from a text file.

    Parameters:
    - file_path (str): Path to the text file.

    Returns:
    - List[str]: List of file content.
    '''

    content = []
    try:
        with open(file_path, 'r') as file:
            content = [line.strip() for line in file.readlines()] # Remove newlines
    except Exception as e:
        raise(e)
    return content

def create_folder_and_return_path(*args):
    # Base directory where folders with the IP will be stored
    destination_path = find_root_directory()
    
    for index, folder in enumerate(args, start=1):
        destination_path = os.path.join(destination_path, folder.lower())
        if not os.path.exists(destination_path):
            os.makedirs(destination_path)
            logging.debug(f'Se ha creado la carpeta {folder} en la ruta {destination_path}')
    
    return destination_path

def save_attendances_to_file(attendances, file):
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

def find_marker_directory(marker, current_path=os.path.abspath(os.path.dirname(__file__))):
    while current_path != os.path.dirname(current_path):  # While not reaching the root of the file system
        #logging.debug(f"Buscando en: {os.path.join(current_path, marker)}")
        if os.path.exists(os.path.join(current_path, marker)):
            return current_path
        current_path = os.path.dirname(current_path)
    
    return None

def find_root_directory():
    path = None
    #logging.debug(f'SE EJECUTA DESDE EXE?: {getattr(sys, 'frozen', False)}')
    if getattr(sys, 'frozen', False):
        path = os.path.dirname(sys.executable)
    else:
        marker = "main.py"
        #logging.debug(path)
        path = find_marker_directory(marker)

    return path

def file_exists_in_folder(file_name, folder):
    from pathlib import Path
    # Create a Path object for the folder and file
    full_path = Path(folder) / file_name
    return full_path.is_file()
