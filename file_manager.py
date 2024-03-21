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

def crear_carpeta_y_devolver_ruta(carpeta1, carpeta2=None, carpeta3=None):
    # Directorio base donde se almacenarán las carpetas con la IP
    directorioActual = os.path.dirname(os.path.abspath(__file__))

    if carpeta2:
        rutaCarpeta1 = os.path.join(directorioActual, carpeta1)
        if not os.path.exists(rutaCarpeta1):
            os.makedirs(rutaCarpeta1)
            logging.debug(f'Se ha creado la carpeta {carpeta1} en la ruta {directorioActual}')
            logging.debug(rutaCarpeta1)
        rutaDestino = os.path.join(os.path.join(directorioActual, carpeta1), carpeta2)
        logging.debug(os.path.join(os.path.join(directorioActual, carpeta1), carpeta2))
    else:
        rutaDestino = os.path.join(directorioActual, carpeta1)
    logging.debug(rutaDestino)
    if not os.path.exists(rutaDestino):
        os.makedirs(rutaDestino)
        logging.debug(f'Se ha creado la carpeta {carpeta2} en la ruta {directorioActual}')

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