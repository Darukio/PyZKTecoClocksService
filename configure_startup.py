import os
import sys
import subprocess
import winreg as reg

def create_service():
    # Obtener la ruta al ejecutable de Python en el entorno virtual
    venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv")
    venv_python = os.path.join(venv_path, "Scripts", "python.exe") if sys.platform == "win32" else os.path.join(venv_path, "bin", "python")

    # Obtener la ruta completa del script service.py
    main_script_path = os.path.abspath("service.py")

    # Instalar el servicio de Windows
    create_service_cmd = [venv_python, main_script_path, "install"]
    subprocess.run(create_service_cmd, check=True)

def configure_startup():
    # Obtener la ruta completa del ejecutable .exe
    exe_path = os.path.join("dist", "main.exe")
    key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
    reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_SET_VALUE)
    if os.path.exists(exe_path):
        # Agregar el script como servicio de Windows
        try:
            reg.SetValueEx(reg_key, "EmsaRelojService", 0, reg.REG_SZ, exe_path)
        except Exception as e:
            print(f"Error al configurar el inicio con Windows: {e}")
    else:
        # Agregar el script Python como servicio de Windows
        pyScriptPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
        try:
            reg.SetValueEx(reg_key, "EmsaRelojService", 0, reg.REG_SZ, f'"{sys.executable}" "{pyScriptPath}"')
        except Exception as e:
            print(f"Error al configurar el inicio con Windows: {e}")
    reg.CloseKey(reg_key)
    print("Configuración de inicio con Windows realizada correctamente.")

if __name__ == "__main__":
    # Crear el servicio
    create_service()

    # Configurar el inicio con Windows
    # configure_startup()