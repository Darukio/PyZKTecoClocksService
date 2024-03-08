import subprocess
import pyuac

@pyuac.main_requires_admin
def main():
    print('Checking Dependencies...')

    # Comando que quieres ejecutar
    comando = 'python -m pip install -q -r requirements.txt && python main.py install'

    subprocess.run(comando, shell=True)

if __name__ == '__main__':
    main()