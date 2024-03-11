import sys
import win32serviceutil
import pyuac
from icon_manager import create_tray_icon
from service import GestorRelojAsistencias
from utils import logging

@pyuac.main_requires_admin
def main():
    logging.debug('Script executing...')

    logFilePath = 'console_log.txt'

    # Redirigir salida estándar y de error al archivo de registro
    sys.stdout = open(logFilePath, 'a')
    sys.stderr = open(logFilePath, 'a')

    if len(sys.argv) == 1:
        tray_icon = create_tray_icon()
        tray_icon.run()
        # servicemanager.Initialize()
        # servicemanager.PrepareToHostSingle(GestorRelojAsistencias)
        # servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(GestorRelojAsistencias)

if __name__ == '__main__':
    main()