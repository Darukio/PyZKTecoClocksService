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
pyinstaller.exe --onefile -n "Gestor Reloj de Asistencias" --windowed -i "energiademisiones.ico" --add-data "resources/*;resources" --debug all main.py
# Instala el servicio y configura la inicialización del servicio cuando se enciende la PC
python configure_startup.py
# Ejecutar main.exe
```

### Instalación de service.py como servicio

YA NO FUNCIONA ASÍ

```bash
# Ejecutar en la consola con permisos de admin
# Instala el servicio
python configure_startup.py
# Para la ejecución del script no es necesario main.py no es necesario permisos de admin, sí '.\venv\Scrs\activate'
python main.py
```

## Explicación de archivos

### Creados por el usuario

-   Con schedule.txt se configura el horario de ejecución del servicio
-   Con file_ips.txt se configura las ips de los dispositivos que el programa va a iterar para la ejecución de las tareas de "actualizar_hora_dispositivo" o "gestionar_marcaciones_dispositivos"

### Generados por el programa

-   En requirements.txt se encuentran las dependencias necesarias para la ejecución del proyecto
-   attendances_file.txt
-   ip_date_file.cro
-   ip_date_logs.cro

#### Logs

-   En program_debug.log se establecen mensajes de depuración, información, advertencias, errores comunes y críticos
-   En program_error.log se establecen mensajes de advertencias, errores comunes y críticos
-   En console_log.txt se guardan los mensajes de la consola que está ejecutando el programa

## Explicación de carpetas

-   devices/ip/
-   venv/
-   resources/
