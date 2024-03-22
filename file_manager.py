import os
from utils import logging

def cargar_desde_archivo(filePath):
    '''
    Carga el contenido desde un archivo de texto.

    Parameters:
    - file_path (str): Ruta del archivo de texto.

    Returns:
    - List[str]: Lista del contenido del archivo.
    '''
    from errors import CargaArchivoFallida

    content = []
    try:
        with open(filePath, 'r') as file:
            content = [line.strip() for line in file.readlines()] # Elimina los saltos de línea
    except CargaArchivoFallida as e:
        raise(e)
    return content

def crear_carpeta_y_devolver_ruta(*args):
    # Directorio base donde se almacenarán las carpetas con la IP
    directorioActual = os.path.dirname(os.path.abspath(__file__))
    rutaDestino = directorioActual
    
    for index, carpeta in enumerate(args, start=1):
        rutaDestino = os.path.join(rutaDestino, carpeta)
        if not os.path.exists(rutaDestino):
            os.makedirs(rutaDestino)
            logging.debug(f'Se ha creado la carpeta {carpeta} en la ruta {rutaDestino}')
    
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

def obtener_directorio_deseado(folder):
    directorioActual = os.path.dirname(os.path.abspath(__file__))
    folderPath = os.path.join(directorioActual, folder)
    return folderPath