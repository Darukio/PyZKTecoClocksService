class DeviceStatusDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Estado de Dispositivos")
        self.setMinimumSize(600, 400)  # Tamaño mínimo recomendado
        self.ping_thread = PingThread(ping_devices)
        self.ping_thread.ping_updated.connect(self.update_table)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels(["IP", "Punto de Marcación", "Nombre de Distrito", "ID", "Estado"])
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)  # Hacer toda la tabla no editable
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  # Ajustar tamaño de columnas según contenido
        self.table_widget.horizontalHeader().setStretchLastSection(True)  # Estirar la última sección para llenar el espacio
        
        layout.addWidget(self.table_widget)

        # Etiqueta para "Actualizando datos"
        self.label_actualizando = QLabel("Actualizando datos...", self)
        self.label_actualizando.setAlignment(Qt.AlignCenter)
        self.label_actualizando.setVisible(False)  # Inicialmente invisible

        layout.addWidget(self.label_actualizando)

        # Etiqueta para "Sin conexiones fallidas"
        self.label_no_fallido = QLabel("Sin conexiones fallidas...", self)
        self.label_no_fallido.setAlignment(Qt.AlignCenter)
        self.label_no_fallido.setVisible(False)  # Inicialmente invisible

        layout.addWidget(self.label_no_fallido)

        # Botón "Actualizar"
        self.btn_actualizar = QPushButton("Actualizar", self)
        self.btn_actualizar.clicked.connect(self.update_data)
        layout.addWidget(self.btn_actualizar, alignment=Qt.AlignCenter)

    def update_data(self):
        self.label_no_fallido.setVisible(False)
        # Mostrar mensaje de "Actualizando datos" en la tabla
        self.label_actualizando.setVisible(True)

        # Iniciar el hilo para obtener datos
        self.ping_thread.start()

    def update_table(self, device_status=None):
        self.label_actualizando.setVisible(False)
        logging.debug(device_status)
        self.table_widget.setSortingEnabled(False)
        self.table_widget.setRowCount(0)  # Limpiar tabla antes de actualizar

        if not device_status:
            logging.debug('ENTRO')
            self.label_no_fallido.setVisible(True)
            return

        for row, (ip, device_info) in enumerate(device_status.items()):
            self.table_widget.insertRow(row)
            self.table_widget.setItem(row, 0, QTableWidgetItem(ip))  # IP

            # Resto de la información del dispositivo
            self.table_widget.setItem(row, 1, QTableWidgetItem(device_info["punto_marcacion"]))
            self.table_widget.setItem(row, 2, QTableWidgetItem(device_info["nombre_distrito"]))
            self.table_widget.setItem(row, 3, QTableWidgetItem(device_info["id"]))

            # Estado
            status_item = QTableWidgetItem(device_info["status"])
            if device_info["status"] == "Conexión fallida":
                status_item.setBackground(QColor(Qt.red))
            elif device_info["status"] == "Conexión exitosa":
                status_item.setBackground(QColor(Qt.green))

            self.table_widget.setItem(row, 4, status_item)

        #self.table_widget.resizeColumnsToContents()  # Ajustar ancho de columnas automáticamente
        self.table_widget.setSortingEnabled(True)
        
    def reject(self):
        self.ping_thread.terminate()  # Detener el hilo cuando se cierra la ventana
        super().reject()

class DeviceAttendancesCountDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cantidad de Marcaciones")
        self.setMinimumSize(600, 400)  # Tamaño mínimo recomendado
        # Establecer icono de la ventana
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "energiademisiones.ico")  # Ruta del archivo del ícono
        self.setWindowIcon(QIcon(file_path))
        self.ping_thread = PingThread(obtener_cantidad_marcaciones_dispositivos)
        self.ping_thread.ping_updated.connect(self.update_table)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels(["IP", "Punto de Marcación", "Nombre de Distrito", "ID", "Cant. de Marcaciones"])
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)  # Hacer toda la tabla no editable
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  # Ajustar tamaño de columnas según contenido
        self.table_widget.horizontalHeader().setStretchLastSection(True)  # Estirar la última sección para llenar el espacio

        # Permitir ordenamiento por clic en los encabezados de las columnas
        self.table_widget.setSortingEnabled(True)

        layout.addWidget(self.table_widget)

        # Etiqueta para "Actualizando datos"
        self.label_actualizando = QLabel("Actualizando datos...", self)
        self.label_actualizando.setAlignment(Qt.AlignCenter)
        self.label_actualizando.setVisible(True)  # Inicialmente invisible

        layout.addWidget(self.label_actualizando)
        # Mostrar mensaje de "Actualizando datos" en la tabla
        self.label_actualizando.setVisible(True)
        # Iniciar el hilo para obtener datos
        self.ping_thread.start()

    def update_table(self, device_status=None):
        self.label_actualizando.setVisible(False)
        logging.debug(device_status)

        if not device_status:
            return

        self.table_widget.setRowCount(0)  # Limpiar tabla antes de actualizar
        for row, (ip, device_info) in enumerate(device_status.items()):
            self.table_widget.insertRow(row)
            self.table_widget.setItem(row, 0, QTableWidgetItem(ip))  # IP

            # Resto de la información del dispositivo
            self.table_widget.setItem(row, 1, QTableWidgetItem(device_info["punto_marcacion"]))
            self.table_widget.setItem(row, 2, QTableWidgetItem(device_info["nombre_distrito"]))
            self.table_widget.setItem(row, 3, QTableWidgetItem(device_info["id"]))
            self.table_widget.setItem(row, 4, QTableWidgetItem(device_info["cant_marcaciones"]))

    def reject(self):
        self.ping_thread.terminate()  # Detener el hilo cuando se cierra la ventana
        super().reject()