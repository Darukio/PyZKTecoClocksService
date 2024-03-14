import os
import subprocess
from pystray import MenuItem as item
from pystray import Icon, Menu
from PIL import Image
from service import is_service_running
from tasks_device_manager import actualizar_hora_dispositivos, gestionar_marcaciones_dispositivos
from utils import logging

# Crear ícono en la bandeja del sistema
def create_tray_icon():
    '''
        Si el servicio está en ejecución,
        el icono es un círculo verde. Sino,
        el ícono es un círculo rojo
    '''
    initial_color = "green" if is_service_running() else "red"
    filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", f"circle-{initial_color}.png")
    image = Image.open(filePath)
    
    try:
        icon = Icon("GestorRelojAsistencias", image, "Gestor Reloj de Asistencias", menu=Menu(
            item('Iniciar', start_service),
            item('Detener', stop_service),
            item('Reiniciar', restart_service),
            item('Actualizar hora', actualizar_hora_dispositivos),
            item('Obtener marcaciones', gestionar_marcaciones_dispositivos),
            item('Salir', exit_icon)
        ))
    except Exception as e:
        logging.error(e)

    return icon

def exit_icon(icon, item):
    # Función para salir del programa
    if is_service_running():
        stop_service(icon)
    try:
        icon.stop()
    except Exception as e:
        logging.critical(e)

def start_service(icon):
    # Función para iniciar el servicio en segundo plano
    try:
        set_icon_color(icon, "green")
        subprocess.run(["net", "start", "GestorRelojAsistencias"], shell=True)
    except Exception as e:
        logging.error(e)

def stop_service(icon):
    # Función para detener el servicio
    set_icon_color(icon, "red")
    subprocess.run(["net", "stop", "GestorRelojAsistencias"], shell=True)

def restart_service(icon):
    # Función para reiniciar el servicio
    stop_service(icon)
    start_service(icon)

def set_icon_color(icon, color):
    # Función para cambiar el color del ícono
    filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", f"circle-{color}.png")
    image = Image.open(filePath)
    icon.update_menu()
    icon.icon = image