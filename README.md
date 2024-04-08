# emsaAttendancesZkProject

## Instalación

### Instalación de dependencias y Configuración del entorno virtual

```bash
Set-ExecutionPolicy RemoteSigned
# Si es necesario, hacer cd carpeta-de-proyecto
# Ejecutar en la consola con permisos de admin
python install.py # Instala las dependencias en un entorno virtual venv
.\venv\Scripts\activate # Activa el entorno virtual venv
```

### Instalación y Configuración de main.exe

```bash
# Ejecutar en la consola con permisos de admin
pyinstaller.exe --onefile -n "Gestor Reloj de Asistencias" --windowed -i "resources/energiademisiones.ico" --add-data "resources/system tray/*;resources/system tray" --debug all main.py
# Configura la inicialización del ejecutable cuando se enciende la PC
python configure_startup.py
# Ejecutar main.exe
```

### Configuración de inicio del script.py

```bash
# Configura la inicialización del script cuando se enciende la PC
python configure_startup.py
# Para la ejecución del script main.py no es necesario permisos de admin, sí '.\venv\Scrs\activate'
python main.py
```

## Explicación de archivos

### Creados por el usuario

-   Con schedule.txt se configura el horario de ejecución de la tarea "gestionar_marcaciones_dispositivos"
-   Con info_devices.txt se configuran los dispositivos que el programa va a iterar para la ejecución de las tareas de "actualizar_hora_dispositivo" o "gestionar_marcaciones_dispositivos". El archivo .txt posee el siguiente formato:
DISTRITO - MODELO - PUNTO DE MARCACIÓN - IP - Booleano de activación del dispositivo (True or False)
Si se configura el booleano en True, el dispositivo se incluirá en la actualización de horas u obtención de marcaciones. Sino, no

### Generados por el programa

-   En requirements.txt se encuentran las dependencias necesarias para la ejecución del proyecto
-   attendances_file.txt es un archivo global en donde se guardan todas las marcaciones, independiente del distrito, modelo o ip del dispositivo
-   ip_date_file.cro es un archivo donde se guardan todas las marcaciones de un dispositivo (según ip) y fecha de marcación. Se encuentra ubicado en devices/distrito/modelo-punto_de_marcación/. El formato del archivo es:
Hora Error e ip
09:14:27 Conexion fallida con 192.168.113.19
-   errors_date.txt es un archivo donde se guardan todos los errores que surjan de los dispositivos. Se encuentra ubicado en devices/errors/. El formato del archivo es:
Legajo Fecha Hora Status Punch
24 22/03/2024 10:41 1 0

#### Logs

-   En program_debug.log se establecen mensajes de depuración, información, advertencias, errores comunes y críticos
-   En program_error.log se establecen mensajes de advertencias, errores comunes y críticos
-   En console_log.txt se guardan los mensajes de la consola que está ejecutando el programa

## Explicación de carpetas

-   devices/distrito/modelo-punto_de_marcación/ proporciona una jerarquía organizada para localizar fácilmente los diferentes distritos y, dentro de cada distrito, los diversos modelos según los puntos de marcación
-   venv/ alberga el entorno virtual, un espacio aislado que contiene todos los paquetes y dependencias específicos del proyecto Python
-   resources/ contiene todos los recursos utilizados para 
