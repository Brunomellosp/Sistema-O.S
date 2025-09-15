import sys, subprocess

def install_requiments():
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print('Todos pacotes foram instalados com sucesso.')
    except subprocess.CalledProcessError as e:
        print(f'Um erro ocorreu ao instalar as dependecias: {e}')
        print('Tente menualmente com: pip install -r requirements.txt')
        sys.exit(1)

if __name__ == '__main__':
    install_requiments()
