import os
import shutil
import winreg
import logging
from .file_manager import encontrar_directorio_raiz

key_name = 'Gestor Reloj de Asistencias'

def add_to_startup():
    # Ruta al ejecutable que quieres iniciar automáticamente
    executable_path = os.path.join(encontrar_directorio_raiz(), "Gestor Reloj de Asistencias.exe")
    logging.debug(f'executable_path: {executable_path}')

    # Abrir la clave del registro donde se guardan los programas que inician con Windows
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_ALL_ACCESS)
    
    # Establecer el valor del registro para que inicie tu aplicación al inicio
    winreg.SetValueEx(key, key_name, 0, winreg.REG_SZ, executable_path)
    
    # Cerrar la clave del registro
    winreg.CloseKey(key)

def remove_from_startup():
    # Intentar abrir la clave del registro donde se guardan los programas que inician con Windows
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_ALL_ACCESS)
        logging.debug(f'key: {key}')
    except FileNotFoundError as e:
        logging.error(e)
        # Si la clave no existe, salir de la función
        return

    # Intentar eliminar la entrada de inicio automático si existe
    try:
        winreg.DeleteValue(key, key_name)
    except FileNotFoundError as e:
        # Si la entrada no existe, también podemos salir de la función
        logging.error(e)
    
    # Cerrar la clave del registro
    winreg.CloseKey(key)

def is_startup_entry_exists():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, key_name)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except WindowsError:
        return False
