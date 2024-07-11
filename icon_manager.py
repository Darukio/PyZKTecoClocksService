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
import threading
import time
import configparser
import schedule
from PyQt5.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot
from attendances_manager import *
from hour_manager import *
from file_manager import cargar_desde_archivo
from utils import logging
from window_manager import DeviceStatusDialog, DeviceAttendancesCountDialog, DeviceAttendancesDialog

# Para leer un archivo INI
config = configparser.ConfigParser()
config.read('config.ini')  # Lectura del archivo de configuración config.ini

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_running = False  # Variable para indicar si la aplicación está corriendo
        self.schedule_thread = None  # Hilo para ejecutar tareas programadas
        self.checked = eval(config['Device_config']['clear_attendance'])  # Estado del checkbox de eliminación de marcaciones

        self.tray_icon = None  # Variable para almacenar el QSystemTrayIcon
        self.__init_ui()  # Inicialización de la interfaz de usuario
        configurar_schedule()  # Configuración de las tareas programadas

    def __init_ui(self):
        self.setWindowTitle('Ventana principal')  # Título de la ventana principal
        self.setGeometry(100, 100, 400, 300)  # Geometría de la ventana principal (posición y tamaño)

        # Crear y configurar el ícono en la bandeja del sistema
        self.color_icon = "red"  # Color inicial del ícono
        self.__create_tray_icon()  # Creación del ícono en la bandeja del sistema        

    def __create_tray_icon(self):
        '''
        Crear ícono en la bandeja del sistema con un menú contextual personalizado
        '''
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "system tray", f"circle-{self.color_icon}.png")  # Ruta del archivo del ícono

        try:
            self.tray_icon = QSystemTrayIcon(QIcon(file_path), self)  # Creación del QSystemTrayIcon con el ícono y ventana principal asociada
            self.tray_icon.setToolTip("Gestor Reloj de Asistencias")  # Texto al colocar el cursor sobre el ícono

            # Crear un menú contextual personalizado
            menu = QMenu()
            menu.addAction(self.__create_action("Iniciar", lambda: self.__opt_start_execution()))  # Acción para iniciar la ejecución
            menu.addAction(self.__create_action("Detener", lambda: self.__opt_stop_execution()))  # Acción para detener la ejecución
            menu.addAction(self.__create_action("Reiniciar", lambda: self.__opt_restart_execution()))  # Acción para reiniciar la ejecución
            menu.addAction(self.__create_action("Probar conexiones", lambda: self.__opt_test_connections()))  # Acción para probar conexiones
            menu.addAction(self.__create_action("Actualizar hora", lambda: self.__opt_update_devices_time()))  # Acción para actualizar la hora del dispositivo
            menu.addAction(self.__create_action("Obtener marcaciones", lambda: self.__opt_fetch_devices_attendances()))  # Acción para obtener las marcaciones de dispositivos
            menu.addAction(self.__create_action("Obtener cantidad de marcaciones", lambda: self.__opt_show_attendances_count()))  # Acción para mostrar la cantidad de marcaciones

            # Checkbox como QAction con estado verificable
            clear_attendance_action = QAction("Eliminar marcaciones", menu)
            clear_attendance_action.setCheckable(True)  # Hacer el QAction verificable
            clear_attendance_action.setChecked(self.checked)  # Establecer estado inicial del checkbox
            clear_attendance_action.triggered.connect(self.__opt_toggle_checkbox_clear_attendance)  # Conectar acción de cambiar estado del checkbox
            menu.addAction(clear_attendance_action)  # Agregar acción al menú

            menu.addAction(self.__create_action("Salir", lambda: self.__opt_exit_icon()))  # Acción para salir de la aplicación
            self.tray_icon.setContextMenu(menu)  # Asignar menú contextual al ícono

        except Exception as e:
            print(f"Error al crear el ícono en la bandeja del sistema: {e}")

        self.tray_icon.show()  # Mostrar el ícono en la bandeja del sistema

    def __create_action(self, text, function):
        """
        Crear una acción para el menú contextual.
        
        Args:
            text (str): Texto de la acción.
            function (function): Función que se ejecutará al activar la acción.
            
        Returns:
            QAction: Acción creada.
        """
        action = QAction(text, self)  # Crear QAction con el texto y la ventana principal asociada
        action.triggered.connect(function)  # Conectar la acción con la función proporcionada
        return action  # Devolver la acción creada

    def __show_message(self, title, text):
        """
        Mostrar un cuadro de diálogo con un mensaje.

        Args:
            title (str): Título del cuadro de diálogo.
            text (str): Texto del mensaje.
        """
        msg_box = QMessageBox()  # Crear instancia de QMessageBox
        msg_box.setWindowTitle(title)  # Establecer el título del cuadro de diálogo
        msg_box.setText(text)  # Establecer el texto del mensaje
        msg_box.setIcon(QMessageBox.Information)  # Establecer el ícono del cuadro de diálogo (información)
        msg_box.exec_()  # Mostrar el cuadro de diálogo

        # Una vez cerrado el QMessageBox, mostrar el menú contextual nuevamente
        if self.tray_icon:
            self.tray_icon.contextMenu().setVisible(True)

    def __set_icon_color(self, icon, color):
        """
        Cambiar el color del ícono en la bandeja del sistema.

        Args:
            icon (QSystemTrayIcon): Ícono en la bandeja del sistema a modificar.
            color (str): Color a establecer ('red', 'yellow', 'green').
        """
        self.color_icon = color  # Actualizar el color del ícono
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "system tray", f"circle-{self.color_icon}.png")  # Ruta del archivo del ícono con el nuevo color
        icon.setIcon(QIcon(file_path))  # Establecer el nuevo ícono con el color especificado

    def iniciar_cronometro(self):
        """
        Iniciar el cronómetro y devolver el tiempo actual.

        Returns:
            float: Tiempo actual en segundos.
        """
        return time.time()  # Devolver el tiempo actual en segundos

    def finalizar_cronometro(self, tiempo_inicial):
        """
        Finalizar el cronómetro, calcular el tiempo transcurrido y mostrar una notificación.

        Args:
            tiempo_inicial (float): Tiempo inicial obtenido al iniciar el cronómetro.
        """
        tiempo_final = self.iniciar_cronometro()  # Obtener el tiempo final
        tiempo_transcurrido = tiempo_final - tiempo_inicial  # Calcular el tiempo transcurrido
        logging.debug(f'La tarea finalizo en {tiempo_transcurrido:.2f} segundos')
        self.tray_icon.showMessage("Notificación", f'La tarea finalizó en {tiempo_transcurrido:.2f} segundos', QSystemTrayIcon.Information)  # Mostrar notificación con el tiempo transcurrido

    @pyqtSlot()
    def __opt_start_execution(self):
        """
        Opción para iniciar la ejecución de la aplicación.
        """
        self.is_running = True  # Marcar que la aplicación está corriendo
        self.__set_icon_color(self.tray_icon, "green")  # Establecer el color del ícono a verde
        try:
            self.schedule_thread = threading.Thread(target=self.run_schedule)  # Crear hilo para ejecutar run_schedule
            logging.debug('Hilo iniciado...')  # Registro de depuración: hilo iniciado
            self.schedule_thread.start()  # Iniciar el hilo
        except Exception as e:
            logging.critical(e)  # Registro crítico si ocurre un error al iniciar el hilo

    @pyqtSlot()
    def __opt_stop_execution(self):
        """
        Opción para detener la ejecución de la aplicación.
        """
        if self.schedule_thread and self.schedule_thread.is_alive():
            self.schedule_thread.join()  # Esperar a que el hilo termine
        logging.debug('Hilo detenido...')  # Registro de depuración: hilo detenido
        self.__set_icon_color(self.tray_icon, "red")  # Establecer el color del ícono a rojo

    @pyqtSlot()
    def __opt_restart_execution(self):
        """
        Opción para reiniciar la ejecución de la aplicación.
        """
        self.__opt_stop_execution()  # Detener la ejecución actual
        self.__opt_start_execution()  # Iniciar la ejecución nuevamente

    @pyqtSlot()
    def __opt_test_connections(self):
        """
        Opción para probar las conexiones de dispositivos.
        """
        self.__set_icon_color(self.tray_icon, "yellow")  # Establecer el color del ícono a amarillo
        try:
            device_status_dialog = DeviceStatusDialog()  # Obtener estado de los dispositivos
            device_status_dialog.exec_()
            self.__set_icon_color(self.tray_icon, "green" if self.is_running else "red")  # Restaurar color del ícono según estado de ejecución
            # Una vez cerrado el QMessageBox, mostrar el menú contextual nuevamente
            if self.tray_icon:
                self.tray_icon.contextMenu().setVisible(True)
        except Exception as e:
            logging.error(f"Error al mostrar conexiones de dispositivos: {e}")  # Registro de error si falla la operación

    @pyqtSlot()
    def __opt_update_devices_time(self):
        """
        Opción para actualizar la hora en los dispositivos.
        """
        self.__set_icon_color(self.tray_icon, "yellow")  # Establecer el color del ícono a amarillo
        tiempo_inicial = self.iniciar_cronometro()  # Iniciar el cronómetro
        actualizar_hora_dispositivos()  # Llamar a función para actualizar hora en dispositivos (se asume que está definida en otro lugar)
        self.finalizar_cronometro(tiempo_inicial)  # Finalizar el cronómetro y mostrar notificación
        self.__set_icon_color(self.tray_icon, "green" if self.is_running else "red")  # Restaurar color del ícono según estado de ejecución

    @pyqtSlot()
    def __opt_fetch_devices_attendances(self):
        """
        Opción para obtener las marcaciones de los dispositivos.
        """
        self.__set_icon_color(self.tray_icon, "yellow")  # Establecer el color del ícono a amarillo
        try:
            device_attendances_dialog = DeviceAttendancesDialog()
            device_attendances_dialog.exec_()
            self.__set_icon_color(self.tray_icon, "green" if self.is_running else "red")  # Restaurar color del ícono según estado de ejecución
            # Una vez cerrado el QMessageBox, mostrar el menú contextual nuevamente
            if self.tray_icon:
                self.tray_icon.contextMenu().setVisible(True)
        except Exception as e:
            logging.error(f"Error al obtener marcaciones: {e}")  # Registro de error si falla la operación

    @pyqtSlot()
    def __opt_show_attendances_count(self):
        """
        Opción para mostrar la cantidad de marcaciones por dispositivo.
        """
        self.__set_icon_color(self.tray_icon, "yellow")  # Establecer el color del ícono a amarillo
        try:
            device_attendances_count_dialog = DeviceAttendancesCountDialog()
            device_attendances_count_dialog.exec_()
            self.__set_icon_color(self.tray_icon, "green" if self.is_running else "red")  # Restaurar color del ícono según estado de ejecución
            # Una vez cerrado el QMessageBox, mostrar el menú contextual nuevamente
            if self.tray_icon:
                self.tray_icon.contextMenu().setVisible(True)
        except Exception as e:
            logging.error(f"Error al mostrar cantidad de marcaciones: {e}")  # Registro de error si falla la operación

    @pyqtSlot()
    def __opt_toggle_checkbox_clear_attendance(self):
        """
        Opción para alternar el estado del checkbox de eliminar marcaciones.
        """
        self.checked = not self.checked  # Invertir el estado actual del checkbox
        logging.debug(f"Status checkbox: {self.checked}")  # Registro de depuración: estado actual del checkbox
        # Modificar el valor del campo deseado en el archivo de configuración
        config['Device_config']['clear_attendance'] = str(self.checked)
        # Escribir los cambios de vuelta al archivo de configuración
        with open('config.ini', 'w') as config_file:
            config.write(config_file)

    @pyqtSlot()
    def __opt_exit_icon(self):
        """
        Opción para salir de la aplicación.
        """
        if self.tray_icon:
            logging.debug(schedule.get_jobs())  # Registro de depuración: obtener trabajos programados
            if len(schedule.get_jobs()) >= 1:
                self.__opt_stop_execution()  # Detener la ejecución si hay trabajos programados
            self.tray_icon.hide()  # Ocultar el ícono en la bandeja del sistema
            QApplication.quit()  # Salir de la aplicación

def configurar_schedule():
    '''
    Configurar las tareas programadas en base a las horas cargadas desde el archivo.
    '''

    # Ruta del archivo de texto que contiene las horas de ejecución
    file_path = os.path.join(os.path.abspath('.'), 'schedule.txt')
    hours_to_perform = None
    try:
        hours_to_perform = cargar_desde_archivo(file_path)  # Cargar horas desde el archivo (función definida en file_manager)
    except Exception as e:
        logging.error(e)  # Registro de error si falla la operación

    if hours_to_perform:
        # Iterar las horas de ejecución
        for hour_to_perform in hours_to_perform:
            '''
            Ejecutar la tarea de actualizar hora y guardar las 
            marcaciones en archivos (individual y en conjunto)
            en la hora especificada en schedule.txt
            '''

            schedule.every().day.at(hour_to_perform).do(gestionar_marcaciones_dispositivos)  # Programar tarea diaria a la hora especificada