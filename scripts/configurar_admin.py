"""Assistente local de credenciais. Não imprime senha e preserva outras chaves."""
from pathlib import Path
from getpass import getpass
from secrets import token_urlsafe
import re
import sys

root=Path(__file__).resolve().parents[1]
env=root/'.env'
print('AEVIA - configuração de moderação local')
print('A senha é invisível ao digitar. Use pelo menos 16 caracteres.')
password=getpass('Crie sua senha de administrador: ').strip()
if not re.fullmatch(r'[A-Za-z0-9@#_.!\-]{16,128}',password):
    print('Senha inválida: use 16 a 128 caracteres, com letras, números e @ # _ . ! - (sem espaços).')
    sys.exit(1)
confirm=getpass('Repita sua senha: ')
if password!=confirm:
    print('As senhas não conferem. Tente novamente.');sys.exit(1)
original=env.read_text(encoding='utf-8') if env.exists() else ''
lines=[line for line in original.splitlines() if not line.startswith(('ADMIN_PASSWORD=','SESSION_SECRET='))]
lines += ['ADMIN_PASSWORD='+password,'SESSION_SECRET='+token_urlsafe(48)]
env.write_text('\n'.join(lines)+'\n',encoding='utf-8')
try:env.chmod(0o600)
except OSError:pass
print('Pronto. Moderação configurada! Reinicie o servidor AEVIA.')
print('Mantenha o arquivo .env privado e fora do GitHub.')
