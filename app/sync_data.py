"""Sincroniza municípios nacionais (IBGE) e coordenadas aproximadas via dataset MIT."""
import os
from .db import initialize
from .sources import seed, sync_municipalities, count_municipalities

if __name__=='__main__':
    initialize()
    seed()
    if count_municipalities() >= 5500 and os.getenv('AEVIA_FORCE_SYNC','no').lower() not in ('1','yes','true'):
        print(f'Catálogo nacional já disponível: {count_municipalities()} municípios. Reutilizando banco local.')
        raise SystemExit(0)
    try:
        n,coords=sync_municipalities()
        print(f'Catálogo nacional atualizado: {n} municípios; {coords} coordenadas importadas.')
    except Exception as exc:
        print(f'Não foi possível atualizar o catálogo: {type(exc).__name__}.')
        print(f'Usando catálogo local disponível: {count_municipalities()} municípios.')
        print('Verifique a internet e tente executar python -m app.sync_data novamente.')
