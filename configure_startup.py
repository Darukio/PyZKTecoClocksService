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
import sys
import subprocess
import winreg as reg
from utils import logging

def create_service():
    # obtener la ruta al ejecutable de Python en el entorno virtual
    venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv")
    venv_python = os.path.join(venv_path, "Scripts", "python.exe") if sys.platform == "win32" else os.path.join(venv_path, "bin", "python")

    # obtener la ruta completa del script service.py
    main_script_path = os.path.abspath("service.py")

    # instalar el servicio de Windows
    create_service_cmd = [venv_python, main_script_path, "install"]
    subprocess.run(create_service_cmd, check=True)

def configure_startup():
    # obtener la ruta completa del ejecutable .exe
    exe_path = os.path.join("dist", "main.exe")
    key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
    reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_SET_VALUE)
    if os.path.exists(exe_path):
        # agregar el script como servicio de Windows
        try:
            reg.SetValueEx(reg_key, "gestor_reloj_asistencias", 0, reg.REG_SZ, exe_path)
        except Exception as e:
            logging.error(f"Error al configurar el inicio con Windows: {e}")
    else:
        # agregar el script Python como servicio de Windows
        py_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
        venv_activate = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv", "Scripts", "activate")
        startup_command = f'"{sys.executable}" "{py_script_path}"'
        try:
            reg.SetValueEx(reg_key, "activar_entorno_virtual && gestor_reloj_asistencias", 0, reg.REG_SZ, f'"{venv_activate}" ; "{startup_command}"')
        except Exception as e:
            logging.error(f"Error al configurar el inicio con Windows: {e}")
    reg.CloseKey(reg_key)
    logging.info("Configuración de inicio con Windows realizada correctamente.")

def check_startup_configuration():
    key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
    try:
        reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_READ)
        value, _ = reg.QueryValueEx(reg_key, "gestor_reloj_asistencias")
        reg.CloseKey(reg_key)
        if value:
            logging.debug("La configuración de inicio con Windows está correctamente establecida.")
        else:
            logging.debug("La configuración de inicio con Windows no está establecida.")
    except FileNotFoundError:
        logging.error("La clave de registro no se encuentra, por lo que la configuración de inicio con Windows no está establecida.")

if __name__ == "__main__":
    # crear el servicio
    create_service()

    # configurar el inicio con Windows
    # configure_startup()

    # check_startup_configuration()
