from PyQt5.QtWidgets import QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QLabel
from device_manager import ping_devices

class DeviceStatusWindow(QMainWindow):
    def __init__(self, device_status):
        super().__init__()

        self.setWindowTitle('Estado de Dispositivos')
        self.setGeometry(100, 100, 600, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.device_status = device_status
        self.table_widget = QTableWidget()
        self.layout.addWidget(self.table_widget)
        self.update_device_table()

        # Configurar un QTimer para actualizar la tabla cada 5 segundos
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_device_table)
        self.timer.start(5000)  # Actualizar cada 5 segundos (5000 ms)

    def update_device_table(self):
        self.device_status = ping_devices()

        # Limpiar la tabla antes de actualizar
        self.table_widget.clear()
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(['Dispositivo', 'Estado'])
        self.table_widget.horizontalHeader().setStretchLastSection(True)

        # Agregar filas a la tabla según la información de los dispositivos
        for device, status in self.device_status.items():
            row_position = self.table_widget.rowCount()
            self.table_widget.insertRow(row_position)

            device_item = QTableWidgetItem(device)
            status_item = QTableWidgetItem(status)

            self.table_widget.setItem(row_position, 0, device_item)
            self.table_widget.setItem(row_position, 1, status_item)