
import sys
from icon_manager import TrayApp
from utils import logging
import configparser

# Versión del programa
VERSION = "v1.0.0-beta"

# Para leer un archivo INI
config = configparser.ConfigParser()
config.read('config.ini')

def main():
    logging.debug('Script executing...')
    logging.info(f"Version del programa: {VERSION}")

    log_config()

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

def log_config():
    for section in config.sections():
        logging.info(f'Section: {section}')
        # Iterar sobre las claves y valores dentro de cada sección
        for key, value in config.items(section):
            logging.info(f'Subsection: {key}, Value: {value}')

if __name__ == '__main__':
    main()