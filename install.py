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
