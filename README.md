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
pyinstaller --noconsole --clean --version-file version_info.txt --onefile --hidden-import=eventlet.hubs.epolls --hidden-import=eventlet.hubs.kqueue --hidden-import=eventlet.hubs.selects --hidden-import=dns --hidden-import=dns.dnssec --hidden-import=dns.e164 --hidden-import=dns.hash --hidden-import=dns.namedict --hidden-import=dns.tsigkeyring --hidden-import=dns.update --hidden-import=dns.version --hidden-import=dns.zone --hidden-import=dns.versioned --add-data "json/errors.json;json/" --noupx --log-level=INFO --debug all schedulerService.py
```

### Instalación de aplicación .exe
```bash
# Ejecutar en cmd o PowerShell con permisos de admin
pyinstaller.exe --noconsole --clean --version-file version_info.txt --onefile --hidden-import=eventlet.hubs.epolls --hidden-import=eventlet.hubs.kqueue --hidden-import=eventlet.hubs.selects --hidden-import=dns --hidden-import=dns.dnssec --hidden-import=dns.e164 --hidden-import=dns.hash --hidden-import=dns.namedict --hidden-import=dns.tsigkeyring --hidden-import=dns.update --hidden-import=dns.version --hidden-import=dns.zone --hidden-import=dns.versioned -n "Servicio Reloj de Asistencias" -i "resources/24-7.png" --add-data "resources/system_tray/*;resources/system_tray" --add-data "resources/24-7.png;resources/" --add-data "json/errors.json;json/" --noupx --log-level=INFO --uac-admin --debug all main.py
```