import os
import json
import requests
from slugify import slugify  # pip install python-slugify

# --- CONFIGURAÇÃO DINÂMICA DE CAMINHOS ---
# Pega o caminho da pasta onde este script está salvo (ex: .../arquivosPython)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define os arquivos de entrada e saída na mesma pasta do script
JSON_ENTRADA = os.path.join(BASE_DIR, 'questoes_originais.json')
JSON_SAIDA = os.path.join(BASE_DIR, 'questoes_para_prisma.json')

# Define a pasta de imagens (sobe um nível para ir para a raiz e depois entra em public)
# Se o script está em /donruan/arquivosPython, RAIZ_PROJETO será /donruan
RAIZ_PROJETO = os.path.dirname(BASE_DIR)
PASTA_IMAGENS = os.path.join(RAIZ_PROJETO, 'Dados', 'mat2022/imagensQuestoes')

# Garante que a pasta de destino exista
os.makedirs(PASTA_IMAGENS, exist_ok=True)

def sanitize(text):
    return slugify(text)

def baixar_e_renomear_imagem(url, title, sufixo=""):
    if not url: return None
    
    ext = os.path.splitext(url)[1]
    original_hash = url.split('/')[-1].split('.')[0]
    
    nome_base = sanitize(title)
    novo_nome = f"{nome_base}_{sufixo}_{original_hash}{ext}" if sufixo else f"{nome_base}_{original_hash}{ext}"
    novo_nome = novo_nome.replace("__", "_")
    
    caminho_final = os.path.join(PASTA_IMAGENS, novo_nome)

    if not os.path.exists(caminho_final):
        try:
            print(f"Baixando imagem: {novo_nome}")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                with open(caminho_final, 'wb') as handler:
                    handler.write(response.content)
            else:
                return None
        except Exception:
            return None
            
    return novo_nome

def mapear_json(dados_originais):
    lista_final = []

    for chave_id, questao in dados_originais.items():
        titulo_questao = questao.get("title", chave_id)
        
        # 1. Tratar Imagens do Contexto
        arquivos_locais = []
        if "files" in questao:
            for link in questao["files"]:
                nome_local = baixar_e_renomear_imagem(link, titulo_questao)
                if nome_local:
                    arquivos_locais.append(nome_local)

        # 2. Mapear Alternativas
        alternativas = []
        for alt in questao["alternatives"]:
            url_img_alt = alt.get("file")
            imagem_local_alt = None
            
            if url_img_alt:
                sufixo_alt = f"alt_{alt['letter']}"
                imagem_local_alt = baixar_e_renomear_imagem(url_img_alt, titulo_questao, sufixo_alt)

            alternativas.append({
                "letra": alt["letter"],
                "texto": alt["text"],
                "e_correta": alt["isCorrect"],
                "imagem_url": imagem_local_alt
            })

        # 3. Criar Objeto seguindo o Schema
        obj_prisma = {
            "id_externo": chave_id,
            "title": titulo_questao,
            "banca": "ENEM",
            "ano": questao.get("year"),
            "grande_area": str(questao.get("discipline", "REDACAO")).upper(),
            "disciplina": questao.get("discipline"),
            "contexto": questao.get("context"),
            "introducao_alternativas": questao.get("alternativesIntroduction"),
            "assunto": questao.get("Subject"),
            "habilidade": questao.get("Ability"),
            "dificuldade": questao.get("Difficulty"),
            "arquivos": arquivos_locais,
            "alternativas": alternativas,
            "interpretacao_contextual": questao.get("ContextualInterpretation", False),
            "consistencia_textual": questao.get("TextualConsistency", False)
        }
        lista_final.append(obj_prisma)
    
    return lista_final

if __name__ == "__main__":
    try:
        print(f"Lendo arquivo: {JSON_ENTRADA}")
        
        if not os.path.exists(JSON_ENTRADA):
            print(f"ERRO: O arquivo 'questoes_originais.json' não está na pasta: {BASE_DIR}")
        else:
            with open(JSON_ENTRADA, 'r', encoding='utf-8') as f:
                dados = json.load(f)

            resultado = mapear_json(dados)

            with open(JSON_SAIDA, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, indent=4, ensure_ascii=False)

            print(f"\nSucesso!")
            print(f"Total de questões: {len(resultado)}")
            print(f"Imagens salvas em: {PASTA_IMAGENS}")
            print(f"JSON gerado em: {JSON_SAIDA}")

    except Exception as e:
        print(f"Erro crítico no processamento: {e}")