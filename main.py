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

import eventlet
eventlet.monkey_patch()
from schedulerService import check_and_install_service
import ctypes
import subprocess
from scripts.ui.message_box import MessageBox
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication
from scripts.ui.icon_manager import MainWindow
from scripts.utils.logging import config_log, logging
from scripts.utils.file_manager import encontrar_directorio_raiz
import sys
import os
import psutil

# Versión del programa
VERSION = "v2.1.22"

# Para leer un archivo INI
from scripts import config
config.read(os.path.join(encontrar_directorio_raiz(), 'config.ini'))

def obtener_proceso_padre(pid):
    """
    Obtiene el proceso padre de un proceso dado.

    Args:
        pid (int): PID del proceso.

    Returns:
        psutil.Process: Objeto del proceso padre o None si no existe.
    """
    try:
        proceso = psutil.Process(pid)
        return proceso.parent()
    except psutil.NoSuchProcess:
        print(f"No existe el proceso con PID {pid}.")
        return None
    
def obtener_procesos_hijos(pid):
    """
    Obtiene una lista de procesos hijos de un proceso dado.

    Args:
        pid (int): PID del proceso.

    Returns:
        list: Lista de objetos psutil.Process que representan los hijos.
    """
    try:
        proceso = psutil.Process(pid)
        return proceso.children()
    except psutil.NoSuchProcess:
        print(f"No existe el proceso con PID {pid}.")
        return []

def is_user_admin():
    """
    Verifica si el proceso tiene privilegios de administrador.
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        print(f"Error al verificar privilegios: {e}")
        return False

def run_as_admin():
    """
    Relanza el script con privilegios de administrador si es necesario.
    """
    if not is_user_admin():
        # El script no se está ejecutando como administrador, por lo tanto, lo reiniciamos con privilegios elevados
        script = sys.argv[0]
        params = " ".join(sys.argv[1:])

        logging.debug("script: "+script
            + " " + params)

        # Ejecutar el script con permisos elevados
        if script.endswith(".exe"):  # Si es un archivo .exe
            # Re-ejecutar el script con permisos de administrador
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        else:  # Si es un script de Python
            subprocess.run(['powershell', 'Start-Process', 'pythonw', '-ArgumentList', f'"{script}" {params}', '-Verb', 'RunAs'])
        sys.exit(0)  # Finaliza el proceso original

def verificar_instancia_duplicada(script_name):
    # Obtener el nombre del script sin la ruta completa
    script_basename = os.path.basename(script_name)
    
    # Iterar sobre todos los procesos activos
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Ignorar procesos de otros programas que no sean el script actual
            if proc.info['name'] == 'python.exe' or proc.info['name'] == 'pythonw.exe':
                # Verificamos si la instancia del script ya está corriendo
                if script_basename in proc.info['cmdline']:
                    if proc.info['pid'] != os.getpid():
                        # Si encontramos otra instancia que no es la actual
                        logging.info(f"Instancia duplicada encontrada: {proc.info['cmdline']}")
                        MessageBox(QMessageBox.Warning, "Ya hay una instancia de la aplicación en ejecución.").exec_()
                        return True
            if proc.info['name'] == script_basename:
                if (
                    proc.info['pid'] != os.getpid()  # No es el proceso actual
                    and proc.info['pid'] != obtener_proceso_padre(os.getpid()).pid  # No es el proceso padre
                    and proc.info['pid'] not in [p.pid for p in obtener_procesos_hijos(os.getpid())]  # No es un proceso hijo
                ):
                    # Si encontramos otra instancia que no es la actual ni está relacionada
                    logging.info(f"Instancia duplicada encontrada: {proc.info['cmdline']}")
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # Si no encontramos una instancia duplicada, devolvemos False
    return False

def cerrar_instancia_duplicada():
    print("Cerrando instancia duplicada...")
    sys.exit(0)  # Salir del script si se encuentra duplicado

def main():
    config_log()

    import os
    logging.debug('Script executing...')

    # Nombre del script actual
    script_name = sys.argv[0]

    logging.debug(script_name)
    
    logging.debug(os.getcwd())
    logging.debug(f'ADMIN: {is_user_admin()}')

    if not is_user_admin():
        run_as_admin()

    # Verificar si ya está ejecutándose una instancia duplicada
    if verificar_instancia_duplicada(script_name):
        cerrar_instancia_duplicada()

    check_and_install_service()
        
    MODE = 'User' if getattr(sys, 'frozen', False) else 'Developer'
    msg_init = f"Program version: {VERSION} - Mode: {MODE}"
    logging.info(msg_init)
    print(msg_init)
    print_copyright()

    config_log_console()
    config_content()
    logging.debug(sys.argv)
    try:
        app = QApplication(sys.argv)
        main_window = MainWindow()
        sys.exit(app.exec_())
    except Exception as e:
        logging.critical(e)

def config_content():
    for section in config.sections():
        logging.debug(f'Section: {section}')
        # Iterar sobre las claves y valores dentro de cada sección
        for key, value in config.items(section):
            logging.debug(f'Subsection: {key}, Value: {value}')

def config_log_console():
    log_file_path = os.path.join(encontrar_directorio_raiz(), 'logs', 'console_log.txt')
    logging.debug(encontrar_directorio_raiz())
    logging.debug(sys.executable)
    
    # Asegúrate de que el archivo de log y su directorio existen
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    if not os.path.exists(log_file_path):
        with open(log_file_path, 'w') as f:
            pass  # Crear el archivo si no existe

    # Redirigir salida estándar y de error al archivo de registro
    sys.stdout = open(log_file_path, 'a')
    sys.stderr = open(log_file_path, 'a')

def print_copyright():
    copyright_text = """
PyZKTecoClocks: GUI for managing ZKTeco clocks. 
Copyright (C) 2024 Paulo Sebastian Spaciuk (Darukio)

This software is licensed under the GNU General Public License v3.0 or later.
It comes without warranty. See <https://www.gnu.org/licenses/> for details."""
    print(copyright_text)
    logging.info(copyright_text)

if __name__ == '__main__':
    main()