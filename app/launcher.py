"""Inicia a versão local correta e evita confusão com servidores antigos."""
import os
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser

PORT=int(os.getenv('AEVIA_PORT','8017'))
EXPECTED='1.7.0'
URL=f'http://127.0.0.1:{PORT}'

def run():
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1',PORT))==0:
            print(f'\nERRO: A porta {PORT} ja esta em uso.\nFeche a outra janela do AEVIA e tente novamente.')
            print('A VERSAO NOVA nao sera confundida com um servidor antigo.\n')
            return 2
    print('\nAEVIA v1.7.0 - BETA SEGURA / ACERVO NACIONAL')
    print('Aguardando o servidor na porta',PORT,'...')
    command=[sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(PORT)]
    process=subprocess.Popen(command)
    try:
        for _ in range(90):
            if process.poll() is not None:
                print('ERRO: servidor terminou durante a inicializacao.');return process.returncode or 1
            try:
                with urllib.request.urlopen(URL+'/api/status',timeout=.7) as response:
                    import json
                    status=json.load(response)
                if status.get('version')==EXPECTED:
                    print('\nVERSAO CONFIRMADA:',EXPECTED)
                    print('SITE:',URL)
                    print('O navegador sera aberto automaticamente. Mantenha este terminal aberto.\n')
                    webbrowser.open(URL)
                    break
                else:
                    print('ERRO: a porta respondeu com outra versao:',status.get('version'))
                    return 2
            except Exception:
                time.sleep(.2)
        else:
            print('ERRO: a aplicacao nao respondeu apos a inicializacao.');return 1
        return process.wait()
    except KeyboardInterrupt:
        print('Encerrando o AEVIA...')
        return 0
    finally:
        if process.poll() is None:
            process.terminate()
            try:process.wait(timeout=4)
            except subprocess.TimeoutExpired:process.kill()

if __name__=='__main__':
    sys.exit(run())
