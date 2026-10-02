import os
import json
import urllib.request
import re
import ast
from openai import OpenAI
from dotenv import load_dotenv
from prompts_base import prompt_base_linguagens_codigos, prompt_base_ciencias_humanas, prompt_base_ciencias_da_natureza, prompt_base_matematica

# --- CONFIGURAÇÃO DE CAMINHOS SEGUROS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_ENTRADA = os.path.join(BASE_DIR, 'questoes_prontas_para_LLM.json')

grande_area_atual = "Linguagens"
disciplina_atual = "interpretacaodetexto"

PASTA_QUESTOES_RAIZ = os.path.join(BASE_DIR, 'Questoes', grande_area_atual.upper(), disciplina_atual)



# --- CONTROLE DE RETOMADA DOS LOTES ---
# Altere para o número do lote de onde deseja iniciar/recomeçar
LOTE_INICIAL = 1

ENV_PATH = os.path.join(os.path.dirname(BASE_DIR), '.env') # Procura o .env na raiz do projeto
load_dotenv(ENV_PATH)

# --- INICIALIZAÇÃO DO CLIENTE COMPATÍVEL COM OPENAI (MARITACA AI) ---
client = OpenAI(
    api_key=os.getenv("MARITACA_API_KEY"),
    base_url="https://chat.maritaca.ai/api/v1"
)

def sanitize_slug(text):
    """ Substitui o python-slugify usando apenas funções nativas """
    text = text.lower()
    text = re.sub(r'[áàãâä]', 'a', text)
    text = re.sub(r'[éèêë]', 'e', text)
    text = re.sub(r'[íìîï]', 'i', text)
    text = re.sub(r'[óòõôö]', 'o', text)
    text = re.sub(r'[úùûü]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[^a-z0-9_-]', '_', text)
    return re.sub(r'_+', '_', text).strip('_')

def baixar_imagem_nativa(url, title, destino_pasta, sufixo=""):
    if not url: 
        return None
    try:
        ext = os.path.splitext(url.split('?')[0])[1]
        if not ext or len(ext) > 5:
            ext = ".png"
            
        original_hash = url.split('/')[-1].split('.')[0][:15]
        nome_base = sanitize_slug(title)
        
        if sufixo:
            novo_nome = f"{nome_base}_{sufixo}_{original_hash}{ext}".replace("__", "_")
        else:
            novo_nome = f"{nome_base}_{original_hash}{ext}".replace("__", "_")
            
        caminho_final = os.path.join(destino_pasta, novo_nome)

        if not os.path.exists(caminho_final):
            print(f"    📥 Baixando imagem: {novo_nome}")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                with open(caminho_final, 'wb') as handler:
                    handler.write(response.read())
                    
        return novo_nome
    except Exception as e:
        print(f"    ⚠️ Falha ao baixar mídia {url}: {e}")
        return None

def processar_e_criar_lotes_dinamicos(tamanho_lote=50):
    if not os.path.exists(JSON_ENTRADA):
        print(f"❌ ERRO: O arquivo de entrada '{JSON_ENTRADA}' não existe.")
        return

    with open(JSON_ENTRADA, 'r', encoding='utf-8') as f:
        dados_entrada = json.load(f)

    if isinstance(dados_entrada, dict):
        itens_questoes = list(dados_entrada.values())
    else:
        itens_questoes = dados_entrada
        
    total = len(itens_questoes)
    print(f"📦 Total de questões estruturadas localizadas para processamento: {total}")

    bloco_atual = []
    
    # Lógica de retomada: calcula o ponto de corte com base no LOTE_INICIAL
    indice_corte_inicial = (LOTE_INICIAL - 1) * tamanho_lote
    contador_lotes = LOTE_INICIAL

    print(f"⏭️ Retomando a partir do LOTE {LOTE_INICIAL} (Pulando as primeiras {indice_corte_inicial} questões)...")

    for idx, q_orig in enumerate(itens_questoes, 1):
        # Pula as questões processadas nos lotes anteriores
        if idx <= indice_corte_inicial:
            continue

        # 1. Configuração do ambiente dinâmico do lote atual
        nome_lote = f"loteEnem{contador_lotes}"
        pasta_lote_atual = os.path.join(PASTA_QUESTOES_RAIZ, nome_lote)
        pasta_imagens_lote = os.path.join(pasta_lote_atual, 'imagensQuestoes')
        caminho_json_lote = os.path.join(pasta_lote_atual, f"questoes_{nome_lote}.json")
        
        os.makedirs(pasta_imagens_lote, exist_ok=True)

        titulo_questao = q_orig.get("title", f"Questão {idx}")
        print(f"🧠 [{idx}/{total}] Classificando no Sabiá: {titulo_questao}...")

        # Coleta os dados prontos diretamente do arquivo de entrada
        assunto = q_orig.get("assunto", disciplina_atual)
        interp_context = q_orig.get("interpretacao_contextual", True)
        consist_text = q_orig.get("consistencia_textual", True)

        # 2. Preparação do conteúdo para a IA (Contexto + Enunciado)
        contexto_txt = q_orig.get("contexto", "")
        intro_txt = q_orig.get("introducao_alternativas", "")
        corpo_questao = f"Contexto/Imagens: {contexto_txt}\nEnunciado: {intro_txt}"
        
        prompt_final = f"{prompt_base_linguagens_codigos}\n\nQuestão para análise:\n{corpo_questao}"

        try:
            response = client.chat.completions.create(
                model="sabiazinho-4",
                messages=[{"role": "user", "content": prompt_final}],
                temperature=0,
            )
            res_ia = response.choices[0].message.content.strip()
            dados_classificacao = ast.literal_eval(res_ia)
            
            # Mapeia as posições da lista reduzida de 3 elementos
            competencia = dados_classificacao[0]
            habilidade = dados_classificacao[1]
            dificuldade = dados_classificacao[2]
        except Exception as e:
            print(f"    ⚠️ Erro ao classificar. Utilizando os valores originais/padrão do arquivo. Erro: {e}")
            competencia = q_orig.get("competencia", 1)
            habilidade = q_orig.get("habilidade", "H1")
            dificuldade = q_orig.get("dificuldade", "Médio")

        # 3. Download das imagens de contexto/enunciado (Chave: 'arquivos')
        arquivos_locais = []
        links_arquivos = q_orig.get("arquivos", [])
        if isinstance(links_arquivos, list):
            for link in links_arquivos:
                nome_local = baixar_imagem_nativa(link, titulo_questao, pasta_imagens_lote)
                if nome_local:
                    arquivos_locais.append(nome_local)

        # 4. Download das imagens das alternativas seguindo rigidamente o modelo Prisma
        alternativas_mapeadas = []
        lista_alts_originais = q_orig.get("alternativas", [])
        
        for alt in lista_alts_originais:
            url_img_alt = alt.get("imagem_url")
            imagem_local_alt = None
            
            if url_img_alt and url_img_alt.startswith("http"):
                sufixo_alt = f"alt_{alt['letra']}"
                imagem_local_alt = baixar_imagem_nativa(url_img_alt, titulo_questao, pasta_imagens_lote, sufixo_alt)
            else:
                imagem_local_alt = url_img_alt

            texto_alt = alt.get("texto")
            if texto_alt == "" or texto_alt is None:
                texto_alt = ""

            alternativas_mapeadas.append({
                "letra": alt["letra"],
                "texto": texto_alt,
                "e_correta": bool(alt["e_correta"]),
                "imagem_url": imagem_local_alt
            })

        # 5. Montagem do Objeto mantendo a integridade dos dados originais e novos
        obj_prisma = {
            "id_externo": q_orig.get("id_externo", f"Questão_{idx}"),
            "title": titulo_questao,
            "banca": q_orig.get("banca", "ENEM"),
            "ano": q_orig.get("ano", 2026),
            "grande_area": q_orig.get("grande_area", grande_area_atual),
            "disciplina": q_orig.get("disciplina", disciplina_atual),
            "contexto": contexto_txt,
            "introducao_alternativas": intro_txt,
            "assunto": assunto,
            "competencia": competencia,
            "habilidade": habilidade,
            "dificuldade": dificuldade,
            "arquivos": arquivos_locais,
            "alternativas": alternativas_mapeadas,
            "interpretacao_contextual": interp_context,
            "consistencia_textual": consist_text
        }

        # 6. Escrita em tempo real (Questão por questão salva instantaneamente no disco)
        bloco_atual.append(obj_prisma)
        with open(caminho_json_lote, 'w', encoding='utf-8') as f:
            json.dump(bloco_atual, f, indent=2, ensure_ascii=False)

        # 7. Divisão de lotes a cada 50 execuções
        if len(bloco_atual) == tamanho_lote or idx == total:
            print(f"💾 {nome_lote.upper()} atualizado e fechado com {len(bloco_atual)} questões.\n")
            bloco_atual = []
            contador_lotes += 1

    print("\n🚀 Script executado com sucesso! Prompt enxuto aplicado e dados preservados.")

if __name__ == "__main__":
    processar_e_criar_lotes_dinamicos(tamanho_lote=50)

