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

import subprocess
import sys
import os
import shutil

def install_requirements():
    # Borrar la carpeta venv si ya existe
    venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv")
    if os.path.exists(venv_path):
        shutil.rmtree(venv_path)

    # Crear un entorno virtual
    subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)

    # Obtener la ruta al ejecutable de Python en el entorno virtual
    venv_python = os.path.join(venv_path, "Scripts", "python.exe") if sys.platform == "win32" else os.path.join(venv_path, "bin", "python")

    # Instalar dependencias desde requirements.txt usando el pip del entorno virtual
    subprocess.run([venv_python, "-m", "pip", "install", "-r", "requirements.txt"], check=True)

if __name__ == "__main__":
    install_requirements()
