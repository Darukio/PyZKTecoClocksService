
import sys
from icon_manager import TrayApp
from utils import logging

# Versión del programa
VERSION = "v1.0.0-beta"

def main():
    logging.debug('Script executing...')
    logging.info(f"Version del programa: {VERSION}")

    logFilePath = 'console_log.txt'

    # Redirigir salida estándar y de error al archivo de registro
    sys.stdout = open(logFilePath, 'a')
    sys.stderr = open(logFilePath, 'a')

    if len(sys.argv) == 1:
        try:
            app = TrayApp()
            app.icon.run()
        except Exception as e:
            logging.error(e)

if __name__ == '__main__':
    main()