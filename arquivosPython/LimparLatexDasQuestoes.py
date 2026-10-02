import os
import json
import base64
from dotenv import load_dotenv
from openai import OpenAI
from slugify import slugify

# --- CONFIGURAÇÃO DE CAMINHOS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAIZ_PROJETO = os.path.dirname(BASE_DIR)

# Pasta onde está o arquivo JSON de entrada (ajuste conforme necessário)
PASTA_DADOS = os.path.join(RAIZ_PROJETO, 'Dados', 'mat2022')
JSON_ENTRADA = os.path.join(PASTA_DADOS, 'questoes_final_ajustado.json') # Nome do seu arquivo original
JSON_SAIDA = os.path.join(PASTA_DADOS, 'questoes_limpas.json')

ENV_PATH = os.path.join(os.path.dirname(BASE_DIR), '.env')
load_dotenv(ENV_PATH)

client = OpenAI(
    api_key=os.getenv("MARITACA_API_KEY"),
    base_url="https://chat.maritaca.ai/api/v1"
)

def solicitar_correcao_unicode(texto):
    """Solicita à IA a remoção do LaTeX e conversão para texto puro legível"""
    if not texto or len(str(texto).strip()) < 2:
        return texto

    instrucoes = r"""
Você é um revisor técnico. Sua tarefa é LIMPAR o texto, removendo todo o LaTeX e convertendo para texto normal legível (Plain Text/Unicode).

REGRAS:
1. REMOVA os delimitadores de cifrão ($ e $$).
2. MOEDA: O símbolo R$ deve ser mantido como texto normal (ex: R$ 50,00).
3. POTÊNCIAS: Use sobrescritos Unicode (ex: x² em vez de x^2, 3ᵗ⁻¹ em vez de 3^{t-1}).
4. FRAÇÕES: Use a barra comum (ex: 1/2).
5. REMOVA quebras de linha (\n) desnecessárias no meio das frases; o texto deve ser corrido.
6. SÍMBOLOS: Converta \cdot para '·' e \text{ km/h} para 'km/h'.
6. MARCAÇÕES: Não altere as partes com ![][IMAGEM_0], ![][IMAGEM_1], etc pois isso é marcação para uma REGEX no front e não deve ser alterado de nenhuma forma.

Retorne APENAS o texto limpo, sem explicações ou aspas extras. Cada texto lido deve ser retornado apenas limpo e sem textos a mais.
"""

    try:
        response = client.chat.completions.create(
            model="sabiazinho-4",
            messages=[
                {"role": "system", "content": instrucoes},
                {"role": "user", "content": f"Texto: {texto}"}
            ],
            temperature=0,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Erro na API ao processar texto: {e}")
        return texto

def processar_arquivo_json():
    # 1. Verifica se o arquivo de entrada existe
    if not os.path.exists(JSON_ENTRADA):
        print(f"ERRO: Arquivo não encontrado em {JSON_ENTRADA}")
        return

    # 2. Lê os dados
    with open(JSON_ENTRADA, 'r', encoding='utf-8') as f:
        questoes = json.load(f)

    print(f"Iniciando limpeza de {len(questoes)} questões...")

    # 3. Itera sobre as questões para limpar o texto
    for i, q in enumerate(questoes, 1):
        print(f"[{i}/{len(questoes)}] Processando: {q.get('title', 'Questão')}")

        # Limpa Contexto
        if "contexto" in q:
            q["contexto"] = solicitar_correcao_unicode(q["contexto"])
        
        # Limpa Introdução das alternativas
        if "introducao_alternativas" in q:
            q["introducao_alternativas"] = solicitar_correcao_unicode(q["introducao_alternativas"])
        
        # Limpa Texto das Alternativas
        if "alternativas" in q:
            for alt in q["alternativas"]:
                if "texto" in alt:
                    alt["texto"] = solicitar_correcao_unicode(alt["texto"])

    # 4. Salva o resultado
    with open(JSON_SAIDA, "w", encoding="utf-8") as f:
        json.dump(questoes, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Sucesso!")
    print(f"Arquivo atualizado salvo em: {JSON_SAIDA}")

# --- EXECUÇÃO ---
if __name__ == "__main__":
    processar_arquivo_json()