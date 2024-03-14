import logging

# Configurar el sistema de registros básico para program_debug.log
logging.basicConfig(filename='program_debug.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Configurar un controlador adicional para los niveles de warning, error y critical en program_error.log
error_logger = logging.FileHandler('program_error.log')
error_logger.setLevel(logging.WARNING)

# Definir un formato para el controlador adicional
error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
error_logger.setFormatter(error_formatter)

# Agregar el controlador adicional al sistema de registros
logging.getLogger().addHandler(error_logger)

# Ejemplos de registros
# logging.debug('Este es un mensaje de depuración')
# logging.info('Este es un mensaje informativo')
# logging.warning('Este es un mensaje de advertencia')
# logging.error('Este es un mensaje de error')
# logging.critical('Este es un mensaje crítico')
'''
Los niveles son jerarquicos. Si se establece en debug, 
se podran ver los mensajes de debug hasta critical. 
Si se establece en critical, se podran ver solamente 
los mensajes critical
'''