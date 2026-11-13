"""Bloqueios óbvios de pré-publicação; não substitui auditoria técnica."""
from pathlib import Path
from urllib.parse import urlparse
from dotenv import dotenv_values
import sys
p=Path(__file__).resolve().parents[1]
env=dotenv_values(p/'.env')
checks={
 'Senha de administrador configurada':len(env.get('ADMIN_PASSWORD') or '')>=16,
 'Segredo de sessão configurado':len(env.get('SESSION_SECRET') or '')>=32,
 'Endereço público HTTPS':(env.get('PUBLIC_URL') or '').startswith('https://'),
 'Ambiente de produção ativado':env.get('APP_ENV')=='production',
 'E-mail de contato para suporte e direitos': '@' in (env.get('AEVIA_CONTACT_EMAIL') or ''),
 'Plano externo de persistência e backup confirmado':env.get('PERSISTENT_STORAGE_CONFIRMED')=='yes',
 'Política LGPD e licenças revisadas pelo responsável':env.get('LEGAL_REVIEW_CONFIRMED')=='yes',
 'Integrações e testes reais no host final realizados':env.get('LIVE_TESTS_CONFIRMED')=='yes',
}
for name,ok in checks.items():print(('OK ' if ok else 'PENDENTE ')+name)
print('A checagem verifica declarações e formato das configurações; não comprova segurança nem backups.')
sys.exit(0 if all(checks.values()) else 2)
