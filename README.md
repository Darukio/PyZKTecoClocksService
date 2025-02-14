# PyZKTecoClocks

## Instalación

### Archivos necesarios para instalación
-   En requirements.txt se encuentran las dependencias necesarias para la ejecución del proyecto.

### Instalación de dependencias
```bash
# Ejecutar en cmd o PowerShell con permisos de admin
Set-ExecutionPolicy RemoteSigned
# Si es necesario, hacer cd carpeta-de-proyecto
python install.py # Instala las dependencias de forma global
```

### Instalación de servicio .exe
```bash
# Ejecutar en cmd o PowerShell con permisos de admin
pyinstaller --noconsole --onefile --hidden-import=eventlet.hubs.epolls --hidden-import=eventlet.hubs.kqueue --hidden-import=eventlet.hubs.selects --hidden-import=dns --hidden-import=dns.dnssec --hidden-import=dns.e164 --hidden-import=dns.hash --hidden-import=dns.namedict --hidden-import=dns.tsigkeyring --hidden-import=dns.update --hidden-import=dns.version --hidden-import=dns.zone --hidden-import=dns.versioned schedulerService.py
```

### Instalación de aplicación .exe
```bash
# Ejecutar en cmd o PowerShell con permisos de admin
pyinstaller.exe --noconsole --clean --onefile --hidden-import=eventlet.hubs.epolls --hidden-import=eventlet.hubs.kqueue --hidden-import=eventlet.hubs.selects --hidden-import=dns --hidden-import=dns.dnssec --hidden-import=dns.e164 --hidden-import=dns.hash --hidden-import=dns.namedict --hidden-import=dns.tsigkeyring --hidden-import=dns.update --hidden-import=dns.version --hidden-import=dns.zone --hidden-import=dns.versioned -n "Servicio Reloj de Asistencias" -i "resources/24-7.png" --add-data "resources/system_tray/*;resources/system_tray" --add-data "resources/24-7.png;resources/" --log-level=DEBUG --debug all main.py
```

### Jerarquía de carpetas y módulos
.
├───resources/
│   └───system_tray/
└───scripts/
    ├───business_logic/
    │	├───attendances_manager.py
    │   ├───connection.py
    │   ├───device_manager.py
    │   └───hour_manager.py
    ├───ui/
    │	├───icon_manager.py
    │   ├───message_box.py
    │   └───window_manager.py
    └───utils/
     	├───add_to_startup.py
        ├───errors.py
        ├───file_manager.py
        └───logging.py

## Interfaz de la aplicación
La aplicación es un ícono en la bandeja de entrada del sistema, el cual contiene un menú contextual con acciones incluidas. Las posibles acciones están separadas por funcionalidades:

### Acciones del servicio
Hay 3 acciones en el menú contextual asociadas al servicio:
* Iniciar servicio
* Detener servicio
* Reiniciar servicio
    
### Acciones de ejecución manual
* Modificar dispositivos
* Probar conexiones
* Actualizar hora
* Obtener marcaciones
* Obtener cantidad de marcaciones

#### Modificar dispositivos
Abre una ventana en la que permite modificar el archivo info_devices.txt a través de una tabla, la cual contiene aquellos dispositivos que se ejecutarán al presionar las acciones "Probar conexiones", "Actualizar hora", "Obtener marcaciones" u "Obtener cantidad de marcaciones".

La tabla en la que se encuentran los dispositivos es interactiva, al presionar 2 veces sobre un campo permite editarlo. Sin embargo, esto NO edita el archivo info_devices.txt en tiempo real.

La interfaz posee los siguientes botones:
* Cargar: Actualiza la tabla con los dispositivos que se encuentren cargados en info_devices.txt.
* Modificar: Guarda los cambios realizados sobre los dispositivos de la tabla en el archivo info_devices.txt.
* Agregar: Abre una ventana para poder añadir un nuevo dispositivo a la tabla. Solicita: Distrito, Modelo, Punto de marcación, IP y cuál es la forma de Comunicación (TCP o UDP).
* Activar todo: Tilda la casilla de activación de todos los dispositivos de la tabla.
* Desactivar todo: Destilda la casilla de activación de todos los dispositivos de la tabla.

#### Probar conexiones
Abre una ventana en la que, al presionar "Actualizar", prueba las conexiones de todos aquellos dispositivos que se encuentren activos en el archivo info_devices.txt.

#### Actualizar hora
Función que actualiza la hora de todos aquellos dispositivos que se encuentren activos en el archivo info_devices.txt.

Hace uso del archivo config.ini (ver apartado Configuración de la aplicación).

Genera archivos (separados por días) en las carpetas logs/, devices/errors/ y devices/distrito/modelo-punto_de_marcación/ (Ver apartado "Explicación de archivos").

Se añadirán mensajes de error en caso de que la pila del dispositivo se encuentre fallando (u ocurra algún error imprevisto).

#### Obtener marcaciones
Abre una ventana en la que, al presionar "Actualizar", obtiene las marcaciones y actualiza la hora de todos aquellos dispositivos que se encuentren activos en el archivo info_devices.txt. Luego, en el caso de que hayan conexiones que hayan fallado, se habilitan los botones "Reintentar todos" o "Reintentar fallidos".

Hace uso del archivo config.ini (ver apartado "Configuración de la aplicación").
- Puede eliminar marcaciones dependiendo de si se encuentra activado la acción "Eliminar marcaciones" del menú contextual.

Genera archivos (separados por días) en las carpetas logs/, devices/errors/ y devices/distrito/modelo-punto_de_marcación/ (Ver apartado "Explicación de archivos").

Se añadirán mensajes de error en caso de que la conexión no pueda realizarse (u ocurra algún error imprevisto).

#### Obtener cantidad de marcaciones
Abre una ventana en la que, al presionar "Actualizar", obtiene solamente la cantidad de marcaciones de todos aquellos dispositivos que se encuentren activos en el archivo info_devices.txt (NO ELIMINA MARCACIONES).

### Acciones de configuración
* Eliminar marcaciones: Edita el parámetro "clear_attendance" del archivo config.ini. Si está tildado, se eliminarán las marcaciones. Sino, no.
* Iniciar automáticamente: Edita el registro del sistema para que la aplicación pueda iniciarse automáticamente cuando el sistema arranca. Si está tildado, iniciará automáticamente. Sino, no.

### Otras acciones
* Salir: Termina la ejecución del programa.

### Configuración de la aplicación
En el archivo config.ini se pueden hallar varias secciones de configuración (y sus respectivos parámetros), las cuales son:
* Attendance_status: En cada parámetro, relaciona un id con la forma de marcar (status_face, status_fingerprint, status_card). Tipo de dato: Int.
* Cpu_config: En esta sección hay parámetros útiles para la configuración de la cpu en tiempos de ejecución.
    * El parámetro "coroutines_pool_max_size" indica cuántas conexiones de dispositivos se deben realizar a la vez cuando se está ejecutando alguna acción de red. Tipo de dato: Int.
* Device_config: En esta sección hay parámetros útiles para la configuración al momento de acceder a un dispositivo.
    * El parámetro "clear_attendance" indica si se debe eliminar las marcaciones del dispositivo cuando se obtengan a través de la ejecución manual (presionar la acción "Obtener marcaciones"). Tipo de dato: Boolean (True o False).
    * El parámetro "clear_attendance_service" indica si se debe eliminar las marcaciones del dispositivo cuando se obtengan a través del servicio (gobernado por schedule.txt). Tipo de dato: Boolean (True o False).
    * El parámetro "disable_device" indica si se debe bloquear el dispositivo cuando se acceda a este. NO RECOMENDADO, si está activo puede conectarse, bloquear y perder la conexión, el dispositivo queda bloqueado indefinidamente hasta que se lo reinicie. Tipo de dato: Boolean (True o False).
* Program_config: En esta sección hay parámetros útiles para la ejecución del programa.
    * El parámetro "name_attendances_file" establece cuál va a ser el nombre del archivo de marcaciones global cuando este sea generado. Tipo de dato: String. Default: uruguai.txt.
* Network_config: En esta sección hay parámetros útiles para la configuración de operaciones de red.
    * El parámetro "retry_connection" indica cuántas veces la aplicación va a intentar reconectar y realizar alguna operación de red. Tipo de dato: Int. Default: 3.
    * El parámetro "size_ping_test_connection" indica cuántos paquetes van a ser enviados para realizar el test de conexión en la acción "Probar conexiones". Tipo de dato: Int. Default: 5.

## Comportamiento del servicio
-   El servicio automático se inicia cuando la aplicación se ejecuta.
-   Cuando se cierra la aplicación, el servicio NO se detiene, continúa ejecutando su rutina de tareas programadas en el archivo schedule.txt.
-   El servicio SIEMPRE hace uso de todos los dispositivos en info_devices.txt.

### Configuración del servicio
-   El parámetro "clear_attendance_service" de la sección "Device_config" del archivo config.ini indica si el servicio va a eliminar marcaciones cuando ejecuta la tarea programada "gestionar_marcaciones_dispositivos".

## Carpetas generadas
-   devices/distrito/modelo-punto_de_marcación/ proporciona una jerarquía organizada para localizar fácilmente los diferentes distritos y, dentro de cada distrito, los diversos modelos según los puntos de marcación.
-   devices/errors/ contiene aquellos errores referidos a las conexiones de los dispositivos.
-   logs/ contiene todos los archivos logs de la aplicación y el servicio.

## Archivos generados

### Por el usuario
-   Con schedule.txt se configura el horario de ejecución de las tareas programadas "gestionar_marcaciones_dispositivos" y "actualizar_hora_dispositivos". NO MODIFICAR LOS TÍTULOS # Hours for gestionar_marcaciones_dispositivos - # Hours for actualizar_hora_dispositivos.
-   Con info_devices.txt se configuran los dispositivos que el programa va a iterar para la ejecución de las tareas de "actualizar_hora_dispositivo" o "gestionar_marcaciones_dispositivos". El archivo .txt posee el siguiente formato:
    
        DISTRITO - MODELO - PUNTO DE MARCACIÓN - IP - ID DE DISPOSITIVO - TIPO DE CONEXIÓN (TCP o UDP) - ACTIVACIÓN DEL DISPOSITIVO (True o False)
    Si se configura el booleano en True, el dispositivo se incluirá en la actualización de horas u obtención de marcaciones. Sino, no.

### Por el programa
-   uruguai.txt es un archivo global en donde se guardan todas las marcaciones, independiente del distrito, modelo o ip del dispositivo.
-   ip_date_file.cro es un archivo donde se guardan todas las marcaciones de un dispositivo (según ip) y fecha de marcación. Se encuentra ubicado en devices/distrito/modelo-punto_de_marcación/. El formato del archivo es:

        Hora Error e ip
        09:14:27 Conexion fallida con 192.168.113.19
-   errors_date.txt es un archivo donde se guardan todos los errores que surjan de los dispositivos. Se encuentra ubicado en devices/errors/. El formato del archivo es:
    
        Legajo Fecha Hora Status Punch
        24 22/03/2024 10:41 1 0

#### Logs
-   En program_debug.log se establecen mensajes de depuración, información, advertencias, errores comunes y críticos de la aplicación.
-   En program_error.log se establecen mensajes de advertencias, errores comunes y críticos de la aplicación.
-   En console_log.txt se guardan los mensajes de la consola que está ejecutando el programa.
-   En scheduler_debug.txt se guardan los mensajes de depuración, información, advertencias, errores comunes y críticos del servicio.