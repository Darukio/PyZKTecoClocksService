# emsaAttendancesZkProject

## Instalación

### Instalación de dependencias y Configuración del entorno virtual

```bash
# Ejecutar en la consola con permisos de admin
python install.py # Instala las dependencias en un entorno virtual venv
.\venv\Scripts\activate # Activa el entorno virtual venv
```

### Instalación y configuración de main.exe

```bash
# Ejecutar en la consola con permisos de admin
pyinstaller.exe main.py --onefile
# Instala el servicio y configura la inicialización del servicio cuando se enciende la PC
python configure_startup.py
# Ejecutar main.exe
```

### Instalación de main.py como servicio

```bash
# Ejecutar en la consola con permisos de admin
# Instala el servicio
python configure_startup.py
# Para la ejecución del script no es necesario main.py no es necesario permisos de admin, sí '.\venv\Scripts\activate'
python main.py
```
