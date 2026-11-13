"""Triagem básica e triagem opcional por modelo. IA nunca aprova publicação sozinha."""
import base64
import json
import os
from pathlib import Path
import httpx
from PIL import Image


def basic_check(image_path, year, source_reference):
    warnings=[]
    if not source_reference.strip(): warnings.append('Não foi indicada uma fonte verificável para a história/data.')
    if year is None: warnings.append('Ano do registro não informado.')
    if image_path:
        with Image.open(image_path) as photo:
            if min(photo.size)<400: warnings.append('Imagem de baixa resolução.')
    else:
        warnings.append('Contribuição textual, sem fotografia anexada.')
    return {'mode':'regras_locais','status':'revisao_humana','warnings':warnings,
            'disclaimer':'Não confirma local, data ou veracidade histórica.'}


def gemini_triage(image_path, title, story, city, year):
    key=os.getenv('GEMINI_API_KEY','').strip()
    if not key:
        raise RuntimeError('GEMINI_API_KEY não configurada.')
    model=os.getenv('GEMINI_MODEL','gemini-2.5-flash')
    prompt=("Você está ajudando na triagem preliminar de um acervo de história urbana do Brasil. "
      "Não pode provar localização, data ou autenticidade apenas pela foto. "
      "Responda APENAS JSON com as chaves: observacoes_visuais (texto), "
      "inconsistencias_possiveis (array de textos), fontes_necessarias (array de textos), "
      "veredito ('revisar' ou 'sem_indicios_claros'), ressalva (texto). "
      "Nunca aprove automaticamente e nunca diga que a foto é comprovadamente histórica. "
      f"Cidade declarada: {city}. Ano declarado: {year}. Título: {title}. Relato: {story[:900]}")
    parts=[{'text':prompt}]
    if image_path:
        data=Path(image_path).read_bytes()
        parts.append({'inline_data':{'mime_type':'image/jpeg','data':base64.b64encode(data).decode('ascii')}})
    url=f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    with httpx.Client(timeout=35) as client:
        resp=client.post(url,headers={'x-goog-api-key':key},json={
            'contents':[{'parts':parts}],
            'generationConfig':{'responseMimeType':'application/json','temperature':0.1}})
        resp.raise_for_status()
        response=resp.json()
    chunks=response.get('candidates', [{}])[0].get('content',{}).get('parts',[])
    answer=''.join(str(c.get('text','')) for c in chunks)
    try: parsed=json.loads(answer)
    except json.JSONDecodeError: parsed={'texto_modelo':answer[:1600]}
    parsed['observacao']='Sugestões de modelo, não prova documental nem aprovação.'
    return parsed
