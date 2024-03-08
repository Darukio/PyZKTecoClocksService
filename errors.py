import datetime
import os
import importlib

class ConexionFallida(Exception):
    def __init__(self, ipDevice):
        try:
            # Importa el módulo errors de manera dinámica
            from file_manager import crear_carpeta_y_devolver_ruta
            folderPath = crear_carpeta_y_devolver_ruta(ipDevice)
            newtime = datetime.today().date()
            dateString = newtime.strftime("%Y-%m-%d")
            fileName = ipDevice+'_'+dateString+'_logs.txt'
            filePath = os.path.join(folderPath, fileName)
            self.mensaje = f'Conexión fallida con {ipDevice}: {Exception}' 
            with open(filePath, 'a') as file:
                file.write(self.mensaje)
            super().__init__(self.mensaje)
        except ImportError:
            pass
    
class CargaArchivoFallida(Exception):
    def __init__(self, filePath):
        self.mensaje = f'Carga fallida del archivo {filePath}: {Exception}' 
        super().__init__(self.mensaje)