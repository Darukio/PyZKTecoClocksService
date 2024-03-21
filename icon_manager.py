import os
import time
import schedule
from pystray import MenuItem as item
from pystray import Icon, Menu
from PIL import Image
from tasks_device_manager import actualizar_hora_dispositivos, gestionar_marcaciones_dispositivos
from file_manager import cargar_desde_archivo
from utils import logging
import threading

class TrayApp:
    def __init__(self):
        self.is_running = False
        self.colorIcon = "red"
        self.icon = self.create_tray_icon()

    def start_execution(self, icon):
        self.is_running = True
        self.configurar_schedule()
        self.set_icon_color(icon, "green")
        # Inicia un hilo para ejecutar run_pending() en segundo plano
        threading.Thread(target=self.run_schedule).start()

    def run_schedule(self):
        # Función para ejecutar run_pending() en segundo plano
        while self.is_running:
            logging.debug('Service executing...')
            schedule.run_pending()
            time.sleep(1)

    def stop_execution(self, icon):
        self.is_running = False
        schedule.clear()
        self.set_icon_color(icon, "red")

    def restart_execution(self, icon):
        # Función para reiniciar el servicio
        self.stop_execution(icon)
        self.start_execution(icon)

    def create_tray_icon(self):
        '''
            Crear ícono en la bandeja del sistema
        '''
        filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", f"circle-{self.colorIcon}.png")
        image = Image.open(filePath)
        
        try:
            icon = Icon("GestorRelojAsistencias", image, "Gestor Reloj de Asistencias", menu=Menu(
                item('Iniciar', self.start_execution),
                item('Detener', self.stop_execution),
                item('Reiniciar', self.restart_execution),
                item('Actualizar hora', actualizar_hora_dispositivos),
                item('Obtener marcaciones', gestionar_marcaciones_dispositivos),
                item('Salir', self.exit_icon)
            ))
        except Exception as e:
            logging.error(e)

        return icon

    def set_icon_color(self, icon, color):
        # Función para cambiar el color del ícono
        self.colorIcon = color
        filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", f"circle-{self.colorIcon}.png")
        image = Image.open(filePath)
        icon.update_menu()
        icon.icon = image

    def exit_icon(self, icon, item):
        # Función para salir del programa
        try:
            logging.debug(schedule.get_jobs())
            if len(schedule.get_jobs()) >= 1:
                self.stop_execution(self, icon)
            icon.stop()
        except Exception as e:
            logging.critical(e)

    def configurar_schedule(self):
        '''
        Configura las tareas programadas en base a las horas cargadas desde el archivo.
        '''

        # Lee las horas de ejecución desde el archivo de texto
        filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schedule.txt')
        hoursToPerform = None
        try:
            hoursToPerform = cargar_desde_archivo(filePath)
        except Exception as e:
            logging.error(e)

        if hoursToPerform: 
            # Itera las horas de ejecución
            for hourToPerform in hoursToPerform:
                '''
                Ejecuta la tarea de actualizar hora y guardar las 
                marcaciones en archivos (individual y en conjunto)
                en la hora especificada en .at
                '''

                schedule.every().day.at(hourToPerform).do(gestionar_marcaciones_dispositivos)