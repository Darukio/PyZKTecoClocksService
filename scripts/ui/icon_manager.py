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

from ..utils.errors import *
from ..utils.file_manager import *
from ..business_logic.attendances_manager import *
from ..business_logic.hour_manager import *
from scripts import config
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
import logging
import os
import time
import schedule
from PyQt5.QtWidgets import QMainWindow, QSystemTrayIcon, QMenu, QAction, QMessageBox
from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal
from .window_manager import DeviceStatusDialog, DeviceAttendancesCountDialog, DeviceAttendancesDialog, DeviceDialog

config.read('config.ini')  # Lectura del archivo de configuración config.ini

class ScheduleThread(QThread):
    operation_running = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.is_running = True  # Variable para controlar el estado del hilo
        self.operation_running.emit(self.is_running)  # Emitir resultado

    def run(self):
        # Función para ejecutar run_pending() en segundo plano
        try:
            logging.debug('Hilo en ejecucion...')
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Simular trabajo
        except Exception as e:
            logging.error(e)

    def stop(self):
        self.is_running = False
        self.operation_running.emit(self.is_running)  # Cambiar el estado para detener el hilo

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_running = False  # Variable para indicar si la aplicación está corriendo
        self.schedule_thread = None  # Hilo para ejecutar tareas programadas
        self.checked = eval(config['Device_config']['clear_attendance'])  # Estado del checkbox de eliminación de marcaciones

        self.tray_icon = None  # Variable para almacenar el QSystemTrayIcon
        self.__init_ui()  # Inicialización de la interfaz de usuario
        configurar_schedule()  # Configuración de las tareas programadas

        self.__opt_start_execution()

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
        file_path = os.path.join(encontrar_directorio_de_marcador("resources"), "resources", "system_tray", f"circle-{self.color_icon}.png")  # Ruta del archivo del ícono
        logging.debug(file_path)

        try:
            self.tray_icon = QSystemTrayIcon(QIcon(file_path), self)  # Creación del QSystemTrayIcon con el ícono y ventana principal asociada
            self.tray_icon.setToolTip("Gestor Reloj de Asistencias")  # Texto al colocar el cursor sobre el ícono

            # Crear un menú contextual personalizado
            menu = QMenu()
            menu.addAction(self.__create_action("Iniciar", lambda: self.__opt_start_execution()))  # Acción para iniciar la ejecución
            menu.addAction(self.__create_action("Detener", lambda: self.__opt_stop_execution()))  # Acción para detener la ejecución
            menu.addAction(self.__create_action("Reiniciar", lambda: self.__opt_restart_execution()))  # Acción para reiniciar la ejecución
            menu.addAction(self.__create_action("Modificar dispositivos", lambda: self.__opt_modify_devices()))  # Acción para modificar dispositivos
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
        file_path = os.path.join(encontrar_directorio_de_marcador("resources"), "resources", "system_tray", f"circle-{self.color_icon}.png")  # Ruta del archivo del ícono con el nuevo color
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
        self.__update_running_thread(True)  # Marcar que la aplicación está corriendo
        self.__set_icon_color(self.tray_icon, "green")  # Establecer el color del ícono a verde
        try:
            self.schedule_thread = ScheduleThread()
            self.schedule_thread.operation_running.connect(self.__update_running_thread)            
            logging.debug('Hilo iniciado...')  # Registro de depuración: hilo iniciado
            self.schedule_thread.start()
        except Exception as e:
            logging.critical(e)  # Registro crítico si ocurre un error al iniciar el hilo

    def __update_running_thread(self, is_running):
        self.is_running = is_running

    @pyqtSlot()
    def __opt_stop_execution(self):
        """
        Opción para detener la ejecución de la aplicación.
        """
        self.__update_running_thread(False)
        logging.debug(self.schedule_thread)
        if self.schedule_thread and self.schedule_thread.is_running:
            self.schedule_thread.stop()  # Esperar a que el hilo termine
        logging.debug('Hilo detenido...')  # Registro de depuración: hilo detenido
        if self.color_icon != "yellow":
            self.__set_icon_color(self.tray_icon, "red")  # Establecer el color del ícono a rojo

    @pyqtSlot()
    def __opt_restart_execution(self):
        """
        Opción para reiniciar la ejecución de la aplicación.
        """
        self.__opt_stop_execution()  # Detener la ejecución actual
        self.__opt_start_execution()  # Iniciar la ejecución nuevamente

    @pyqtSlot()
    def __opt_modify_devices(self):
        """
        Opción para probar las conexiones de dispositivos.
        """
        self.__set_icon_color(self.tray_icon, "yellow")  # Establecer el color del ícono a amarillo
        try:
            device_dialog = DeviceDialog()  # Obtener estado de los dispositivos
            device_dialog.exec_()
            self.__set_icon_color(self.tray_icon, "green" if self.is_running else "red")  # Restaurar color del ícono según estado de ejecución
            # Una vez cerrado el QMessageBox, mostrar el menú contextual nuevamente
            if self.tray_icon:
                self.tray_icon.contextMenu().setVisible(True)
        except Exception as e:
            logging.error(f"Error al modificar dispositivos: {e}")  # Registro de error si falla la operación

    @pyqtSlot()
    def __opt_test_connections(self):
        """
        Opción para probar las conexiones de dispositivos.
        """
        self.__set_icon_color(self.tray_icon, "yellow")  # Establecer el color del ícono a amarillo
        try:
            device_status_dialog = DeviceStatusDialog()  # Obtener estado de los dispositivos
            device_status_dialog.op_terminated.connect(self.finalizar_cronometro)
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
            device_attendances_dialog.op_terminated.connect(self.finalizar_cronometro)
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
            device_attendances_count_dialog.op_terminated.connect(self.finalizar_cronometro)
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
    file_path = os.path.join(encontrar_directorio_raiz(), 'schedule.txt')
    logging.debug(file_path)

    try:
        content = cargar_desde_archivo(file_path)  # Cargar contenido desde el archivo
    except Exception as e:
        logging.error(e)  # Registro de error si falla la operación
        return

    gestionar_hours = []
    actualizar_hours = []
    current_task = None

    for line in content:
        if line.startswith("#"):
            if "gestionar_marcaciones_dispositivos" in line:
                current_task = "gestionar"
            elif "actualizar_hora_dispositivos" in line:
                current_task = "actualizar"
        elif line:
            if current_task == "gestionar":
                gestionar_hours.append(line)
            elif current_task == "actualizar":
                actualizar_hours.append(line)

    if gestionar_hours:
        # Iterar las horas de ejecución para gestionar_marcaciones_dispositivos
        for hour_to_perform in gestionar_hours:
            schedule.every().day.at(hour_to_perform).do(gestionar_marcaciones_dispositivos)

    if actualizar_hours:
        # Iterar las horas de ejecución para actualizar_hora_dispositivos
        for hour_to_perform in actualizar_hours:
            schedule.every().day.at(hour_to_perform).do(actualizar_hora_dispositivos)