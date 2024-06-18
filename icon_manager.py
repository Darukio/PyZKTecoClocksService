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
import time
import schedule
import configparser
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QIcon
from windows_manager import DeviceStatusWindow
from attendances_manager import *
from hour_manager import *
from file_manager import cargar_desde_archivo
from utils import logging
import threading

# Para leer un archivo INI
config = configparser.ConfigParser()
config.read('config.ini')

class TrayApp:
    def __init__(self):
        self.app = QApplication([])
        self.is_running = False
        self.schedule_thread = None
        self.colorIcon = "red"
        self.checked = eval(config['Device_config']['clear_attendance'])
        self.icon = self.create_tray_icon()
        self.configurar_schedule(self.icon)

    def start_execution(self, icon):
        self.is_running = True
        self.set_icon_color(icon, "green")
        # Inicia un hilo para ejecutar run_pending() en segundo plano
        try:
            self.schedule_thread = threading.Thread(target=self.run_schedule)
            logging.debug('Hilo iniciado...')
            self.schedule_thread.start()
        except Exception as e:
            logging.critical(e)

    def run_schedule(self):
        # Función para ejecutar run_pending() en segundo plano
        try:
            while self.is_running:
                logging.debug('Hilo en ejecucion...')
                schedule.run_pending()
                time.sleep(1)
        except Exception as e:
            logging.error(e)

    def stop_execution(self, icon):
        self.is_running = False
        if self.schedule_thread and self.schedule_thread.is_alive():
            self.schedule_thread.join()  # Esperar a que el hilo termine
        logging.debug('Hilo detenido...')
        # schedule.clear()
        self.set_icon_color(icon, "red")

    def restart_execution(self, icon):
        # Función para reiniciar el servicio
        self.stop_execution(icon)
        self.start_execution(icon)

    def create_tray_icon(self):
        '''
            Crear ícono en la bandeja del sistema
        '''
        filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "system tray", f"circle-{self.colorIcon}.png")
        
        try:
            icon = QSystemTrayIcon(QIcon(filePath), self.app)
            icon.setToolTip("GestorRelojAsistencias")
            # Crear un menú contextual con un elemento de menú verificable (simulando un checkbox)
            menu = QMenu()
            menu.addAction(self.create_action("Iniciar", lambda: self.start_execution(icon)))
            menu.addAction(self.create_action("Detener", lambda: self.stop_execution(icon)))
            menu.addAction(self.create_action("Reiniciar", lambda: self.restart_execution(icon)))
            menu.addAction(self.create_action("Probar conexiones", lambda: self.opc_probar_conexiones(icon)))
            menu.addAction(self.create_action("Actualizar hora", lambda: self.opc_actualizar_hora_dispositivos(icon)))
            menu.addAction(self.create_action("Obtener marcaciones", lambda: self.opc_marcaciones_dispositivos(icon)))
            menu.addAction(self.create_action("Obtener cantidad de marcaciones", lambda: self.mostrar_cantidad_marcaciones(icon)))
            
            # Checkbox como QAction con estado verificable
            clear_attendance_action = QAction("Eliminar marcaciones", menu)
            clear_attendance_action.setCheckable(True)  # Hacer el QAction checkable
            clear_attendance_action.setChecked(self.checked)
            clear_attendance_action.triggered.connect(self.toggle_checkbox_clear_attendance)
            menu.addAction(clear_attendance_action)

            menu.addAction(self.create_action("Salir", lambda: self.exit_icon(icon)))
            icon.setContextMenu(menu)
        except Exception as e:
            logging.error(e)

        return icon

    def create_action(self, text, slot):
        '''
        Crea una acción con un texto y un slot.
        '''
        action = QAction(text, self.app)
        action.triggered.connect(slot)
        return action

    def ventana_estados_dispositivos(device_status):
        window = DeviceStatusWindow(device_status)
        window.show()

    def opc_probar_conexiones(self, icon):
        from device_manager import ping_devices
        self.set_icon_color(icon, "yellow")
        tiempo_inicial = self.iniciar_cronometro()
        device_status = ping_devices()
        threading.Thread(target=self.ventana_estados_dispositivos, args=(device_status,))
        self.finalizar_cronometro(icon, tiempo_inicial)
        self.set_icon_color(icon, "green") if self.is_running else self.set_icon_color(icon, "red")
        return
    
    def opc_actualizar_hora_dispositivos(self, icon):
        self.set_icon_color(icon, "yellow")
        tiempo_inicial = self.iniciar_cronometro()
        actualizar_hora_dispositivos()
        self.finalizar_cronometro(icon, tiempo_inicial)
        self.set_icon_color(icon, "green") if self.is_running else self.set_icon_color(icon, "red")
        return
    
    def iniciar_cronometro(self):
        return time.time()
    
    def finalizar_cronometro(self, icon, tiempo_inicial):
        tiempo_final = self.iniciar_cronometro()
        tiempo_transcurrido = tiempo_final - tiempo_inicial
        icon.showMessage("Notificación", f'La tarea finalizó en {tiempo_transcurrido:.2f} segundos', QSystemTrayIcon.Information)
        return

    def opc_marcaciones_dispositivos(self, icon):
        self.set_icon_color(icon, "yellow")
        tiempo_inicial = self.iniciar_cronometro()
        gestionar_marcaciones_dispositivos()
        self.finalizar_cronometro(icon, tiempo_inicial)
        self.set_icon_color(icon, "green") if self.is_running else self.set_icon_color(icon, "red")
        return

    # Definir una función para cambiar el estado de la checkbox
    def toggle_checkbox_clear_attendance(self, pChecked):
        self.checked = pChecked
        logging.debug(f"Status checkbox: {self.checked}")
        # Modificar el valor del campo deseado
        config['Device_config']['clear_attendance'] = str(self.checked)
        # Escribir los cambios de vuelta al archivo de configuración
        with open('config.ini', 'w') as config_file:
            config.write(config_file)
    
    def mostrar_cantidad_marcaciones(self, icon):
        # Crear una ventana emergente de tkinter
        self.set_icon_color(icon, "yellow")
        try:
            tiempo_inicial = self.iniciar_cronometro()
            cantidad_marcaciones = obtener_cantidad_marcaciones()
            self.finalizar_cronometro(icon, tiempo_inicial)
            cantidad_marcaciones_str = "\n".join([f"{ip}: {cantidad}" for ip, cantidad in cantidad_marcaciones.items()])
            # Mostrar un cuadro de diálogo con la información
            QMessageBox.information(None, "Marcaciones por dispositivo", cantidad_marcaciones_str)
        except Exception as e:
            logging.error(f"Error al mostrar cantidad de marcaciones: {e}")
        finally:
            self.set_icon_color(icon, "green") if self.is_running else self.set_icon_color(icon, "red")

    def set_icon_color(self, icon, color):
        # Función para cambiar el color del ícono
        self.colorIcon = color
        filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "system tray", f"circle-{self.colorIcon}.png")
        icon.setIcon(QIcon(filePath))

    def exit_icon(self, icon):
        # Función para salir del programa
        try:
            logging.debug(schedule.get_jobs())
            if len(schedule.get_jobs()) >= 1:
                self.stop_execution(icon)
            icon.hide()
            self.app.quit()
        except Exception as e:
            logging.critical(e)

    def configurar_schedule(self, icon):
        '''
        Configura las tareas programadas en base a las horas cargadas desde el archivo.
        '''

        # Lee las horas de ejecución desde el archivo de texto
        filePath = os.path.join(os.path.abspath('.'), 'schedule.txt')
        hoursToPerform = None
        try:
            hoursToPerform = cargar_desde_archivo(filePath)
        except Exception as e:
            logging.error(e)

        if hoursToPerform: 
            # Itera las horas de ejecución
            for hourToPerform in hoursToPerform:
                '''
                Ejecuta la tarea de actualizar hora y guarda las 
                marcaciones en archivos (individual y en conjunto)
                en la hora especificada en schedule.txt
                '''

                schedule.every().day.at(hourToPerform).do(gestionar_marcaciones_dispositivos)