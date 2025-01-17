import os
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QIcon

from scripts.utils.file_manager import encontrar_directorio_de_marcador

# Subclase para el diálogo de estado de dispositivos
class MessageBox(QMessageBox):
    def __init__(self, icon, text, parent=None):
        super().__init__(icon, 'Gestor Reloj de Asistencias', text, parent)

        file_path = os.path.join(encontrar_directorio_de_marcador("resources"), "resources", "fingerprint.ico")
        self.setWindowIcon(QIcon(file_path))