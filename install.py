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
    """
    Sets up a Python virtual environment and installs dependencies.
    This function performs the following steps:
    1. Deletes the existing virtual environment folder (`venv`) if it exists.
    2. Creates a new virtual environment in the `venv` directory.
    3. Determines the path to the Python executable within the virtual environment.
    4. Installs the dependencies listed in the `requirements.txt` file using the virtual environment's `pip`.
    Raises:
        subprocess.CalledProcessError: If any subprocess command fails.
    """
    # Delete the venv folder if it already exists
    venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv")
    if os.path.exists(venv_path):
        shutil.rmtree(venv_path)

    # Create a virtual environment
    subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)

    # Get the path to the Python executable in the virtual environment
    venv_python = os.path.join(venv_path, "Scripts", "python.exe") if sys.platform == "win32" else os.path.join(venv_path, "bin", "python")

    # Install dependencies from requirements.txt using the virtual environment's pip
    subprocess.run([venv_python, "-m", "pip", "install", "-r", "requirements.txt"], check=True)

if __name__ == "__main__":
    install_requirements()