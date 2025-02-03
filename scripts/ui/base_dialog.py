from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from scripts.utils.errors import BaseErrorWithMessageBox
from ..utils.file_manager import find_marker_directory
import os

class BaseDialog(QDialog):
    def __init__(self, parent=None, window_title=""):
        try:
            super().__init__(parent)
            self.setWindowTitle(window_title)

            # Set window icon
            self.file_path_resources = os.path.join(find_marker_directory("resources"), "resources")
            self.file_path_icon = os.path.join(self.file_path_resources, "fingerprint.ico")
            self.setWindowIcon(QIcon(self.file_path_icon))
            
            # Allow minimizing the window
            self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
            # Allow maximizing the window
            self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        except Exception as e:
            BaseErrorWithMessageBox(3003, str(e))

    def init_ui(self):
        self.adjust_size()
    
    def adjust_size(self):
        # Adjust window size dynamically based on content
        self.adjustSize()