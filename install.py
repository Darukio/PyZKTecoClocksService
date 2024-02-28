import subprocess

print('Checking Dependencies...')

# Comando que quieres ejecutar en modo administrador
comando = '''
python -m pip install -q -r requirements.txt &
python main.py install &
python main.py start
'''

# Ejecutar el comando en modo administrador
subprocess.run(f'runas /user:Administrator {comando}', shell=True)
