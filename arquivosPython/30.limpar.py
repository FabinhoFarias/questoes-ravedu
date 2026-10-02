import json
import re
import html
import os

def limpar_texto(texto_html):
    if not texto_html:
        return ""
    
    # 1. Converte entidades HTML (&aacute; -> á, etc.)
    texto_convertido = html.unescape(texto_html)
    
    # 2. Substitui sequencialmente as tags <img> por [IMAGEM_0], [IMAGEM_1]...
    contador = 0
    def substituir_img(match):
        nonlocal contador
        marcacao = f" [IMAGEM_{contador}] "
        contador += 1
        return marcacao

    # Procura por qualquer tag <img ...> ou <img ... />
    texto_com_marcacao = re.sub(r'<img[^>]*>', substituir_img, texto_convertido)
    
    # 3. Remove o restante das tags HTML que sobraram (<p>, <span>, etc.)
    texto_limpo = re.sub(r'</?[^>]+(>|$)', '', texto_com_marcacao)
    
    # 4. Remove espaços extras e quebras duplicadas causadas pelas tags
    texto_limpo = re.sub(r'\s+', ' ', texto_limpo)
    
    return texto_limpo.strip()

# --- ENCONTRA A PASTA DO SCRIPT AUTOMATICAMENTE ---
pasta_do_script = os.path.dirname(os.path.abspath(__file__))

nome_entrada = 'questoesBrutasENEM.json'
nome_saida = 'questoes_prontas_para_LLM.json'

grande_area = 'Linguagens'
disciplina = 'interpretacaodetexto'

caminho_entrada = os.path.join(pasta_do_script, nome_entrada)
caminho_saida = os.path.join(pasta_do_script, nome_saida)
# --------------------------------------------------

# 1. Carrega o arquivo da plataforma usando o formato JSON Lines (múltiplos JSONs por linha)
dados_originais = []
with open(caminho_entrada, 'r', encoding='utf-8') as f:
    for linha in f:
        linha = linha.strip()
        if linha:  # Garante que não vai tentar ler linhas vazias
            dados_originais.append(json.loads(linha))

novas_questoes = []

# Itera sobre cada bloco/linha importado do arquivo original
for bloco in dados_originais:
    try:
        questoes_ferretto = bloco['data']['questions']['nodes']
    except (KeyError, TypeError):
        continue

    # 2. Faz a equivalência estrutural para cada questão
    for q in questoes_ferretto:
        banca_nome = q.get('educationalInstitution', {}).get('name', 'Desconhecida') if q.get('educationalInstitution') else 'Desconhecida'
        ano_questao = q.get('year', None)
        codigo = q.get('code', '')
        
        alternativas_mapeadas = []
        letras = ['A', 'B', 'C', 'D', 'E']
        
        for idx, alt in enumerate(q.get('alternatives', [])):
            letra_atual = letras[idx] if idx < len(letras) else str(idx + 1)
            conteudo_alt = alt.get('content', '')
            
            # --- Identifica e isola imagens na alternativa ---
            img_alt_match = re.search(r'src="([^"]+)"', conteudo_alt)
            
            if img_alt_match:
                texto_final_alt = ""
                url_imagem_alt = img_alt_match.group(1).replace('\\', '') # Limpa possíveis barras de escape da string
            else:
                texto_final_alt = limpar_texto(conteudo_alt)
                url_imagem_alt = None

            alternativas_mapeadas.append({
                "letra": letra_atual,
                "texto": texto_final_alt,
                "e_correta": alt.get('rightAnswer', False),
                "imagem_url": url_imagem_alt
            })

        questao_formatada = {
            "id_externo": f"Questao_{q.get('id')}",
            "title": f"Questão {codigo} - {banca_nome.upper()}",
            "banca": banca_nome.upper(),
            "ano": int(ano_questao) if ano_questao else None,
            "grande_area": grande_area,
            "disciplina": q.get('discipline', {}).get('slug', disciplina) if q.get('discipline') else disciplina,
            "contexto": "[IMAGEM_0]" if "img" in q.get('content', '') else "",
            "introducao_alternativas": limpar_texto(q.get('content', '')),
            "assunto": q.get('parentSubject', {}).get('name', '') if q.get('parentSubject') else '',
            "habilidade": "H8",
            "dificuldade": "Médio",
            "arquivos": [],
            "alternativas": alternativas_mapeadas,
            "interpretacao_contextual": True,
            "consistencia_textual": True
        }
        
        urls_imagens = re.findall(r'src="([^"]+)"', q.get('content', ''))
        if urls_imagens:
            questao_formatada["arquivos"] = urls_imagens

        novas_questoes.append(questao_formatada)

# 3. Salva a lista de questões acumulando os dados caso o arquivo já exista e possua conteúdo
if os.path.exists(caminho_saida) and os.path.getsize(caminho_saida) > 0:
    with open(caminho_saida, 'r', encoding='utf-8') as f:
        try:
            lista_acumulada = json.load(f)
        except json.JSONDecodeError:
            lista_acumulada = []
    
    lista_acumulada.extend(novas_questoes)
    total_acumulado = len(lista_acumulada)
else:
    lista_acumulada = novas_questoes
    total_acumulado = len(novas_questoes)

# Salva a lista atualizada no arquivo final na mesma pasta
with open(caminho_saida, 'w', encoding='utf-8') as f:
    json.dump(lista_acumulada, f, ensure_ascii=False, indent=2)

print(f"\n✅ Processadas mais {len(novas_questoes)} questões.")
print(f"📦 Total acumulado no {nome_saida}: {total_acumulado} questões!")