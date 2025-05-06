# PyZKTecoClocks
[![Docs](https://img.shields.io/badge/docs-online-blue.svg)](https://darukio.github.io/PyZKTecoClocks/) [![Program](https://img.shields.io/badge/program-online-blue.svg)](https://github.com/Darukio/PyZKTecoClocks)

## [![Español](https://img.shields.io/badge/language-es-red.svg)](#)

### Instalación

#### Prerrequisitos

- Python 3.7+
- Windows 10 o superior

#### Dependencias

Todos los paquetes necesarios están listados en `requirements.txt`.

```bash
# Ejecutar en cmd o PowerShell con permisos de administrador
Set-ExecutionPolicy RemoteSigned
# Si es necesario, navegar al directorio del proyecto
git clone https://github.com/Darukio/PyZKTecoClocks.git && cd PyZKTecoClocks
git submodule update --remote --recursive
python install.py  # Instala las dependencias de forma global
```

#### Creación de ejecutables

**Ejecutable del servicio:**
```bash
# Ejecutar en cmd o PowerShell con permisos de admin
pyinstaller --noconsole --clean --version-file version_info.txt --onefile --hidden-import=eventlet.hubs.epolls --hidden-import=eventlet.hubs.kqueue --hidden-import=eventlet.hubs.selects --hidden-import=dns --hidden-import=dns.dnssec --hidden-import=dns.e164 --hidden-import=dns.hash --hidden-import=dns.namedict --hidden-import=dns.tsigkeyring --hidden-import=dns.update --hidden-import=dns.version --hidden-import=dns.zone --hidden-import=dns.versioned --add-data "json/errors.json;json/" --noupx --log-level=INFO --debug all schedulerService.py
```

**Interfaz del servicio:**
```bash
# Ejecutar en cmd o PowerShell con permisos de admin
pyinstaller.exe --noconsole --clean --version-file version_info.txt --onefile --hidden-import=eventlet.hubs.epolls --hidden-import=eventlet.hubs.kqueue --hidden-import=eventlet.hubs.selects --hidden-import=dns --hidden-import=dns.dnssec --hidden-import=dns.e164 --hidden-import=dns.hash --hidden-import=dns.namedict --hidden-import=dns.tsigkeyring --hidden-import=dns.update --hidden-import=dns.version --hidden-import=dns.zone --hidden-import=dns.versioned -n "Servicio Reloj de Asistencias" -i "resources/24-7.png" --add-data "resources/system_tray/*;resources/system_tray" --add-data "resources/24-7.png;resources/" --add-data "json/errors.json;json/" --noupx --log-level=INFO --uac-admin --debug all main.py
```
