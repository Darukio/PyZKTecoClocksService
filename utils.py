import logging

# Configurar el sistema de registros
logging.basicConfig(filename='program.log',  # Registra los mensajes en un archivo
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Ejemplos de registros
# logging.debug('Este es un mensaje de depuración')
# logging.info('Este es un mensaje informativo')
# logging.warning('Este es un mensaje de advertencia')
# logging.error('Este es un mensaje de error')
# logging.critical('Este es un mensaje crítico')