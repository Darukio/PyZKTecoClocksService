import os
from utils import logging
from errors import CargaArchivoFallida

def cargar_desde_archivo(filePath):
    '''
    Carga el contenido desde un archivo de texto.

    Parameters:
    - file_path (str): Ruta del archivo de texto.

    Returns:
    - List[str]: Lista del contenido del archivo.
    '''
    content = []
    try:
        with open(filePath, 'r') as file:
            content = [line.strip() for line in file.readlines()] # Elimina los saltos de línea
    except CargaArchivoFallida as e:
        raise(e)
    return content

def crear_carpeta_y_devolver_ruta(ip):
    # Directorio base donde se almacenarán las carpetas con la IP
    directorioActual = os.path.dirname(os.path.abspath(__file__))
    
    directorioDispositivos = os.path.join(directorioActual, 'devices')

    # Crear el directorio con la IP si no existe
    rutaDestino = os.path.join(directorioDispositivos, ip)
    if not os.path.exists(rutaDestino):
        os.makedirs(rutaDestino)
        logging.debug(f'Se ha creado la carpeta {ip} en la ruta {directorioActual}')

    return rutaDestino

def guardar_marcaciones_en_archivo(attendances, file):
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
                formatted_timestamp = attendance.timestamp.strftime("%d/%m/%Y %H:%M") # Formatea el timestamp a DD/MM/YYYY hh:mm, ejemplo: 21/07/2023 05:28
                f.write(f"{attendance.user_id} {formatted_timestamp} {attendance.status} {attendance.punch}\n")
    except Exception as e:
        logging.error(f'Process terminate: {e}')
        