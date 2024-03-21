
import sys
import pyuac
from icon_manager import TrayApp
from utils import logging

@pyuac.main_requires_admin
def main():
    logging.debug('Script executing...')

    logFilePath = 'console_log.txt'

    # Redirigir salida estándar y de error al archivo de registro
    sys.stdout = open(logFilePath, 'a')
    sys.stderr = open(logFilePath, 'a')

    if len(sys.argv) == 1:
        app = TrayApp()
        app.icon.run()

if __name__ == '__main__':
    main()