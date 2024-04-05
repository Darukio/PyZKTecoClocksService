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
    
class CargaArchivoFallida(Exception):
    def __init__(self, filePath):
        self.mensaje = f'Carga fallida del archivo {filePath}: {str(Exception)}' 
        super().__init__(self.mensaje)