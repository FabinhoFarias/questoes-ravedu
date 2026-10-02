import json
import os
import re
from dotenv import load_dotenv
from openai import OpenAI

# --- CONFIGURAÇÃO DE CAMINHOS ---
# Garante que o script encontre os arquivos na pasta onde ele está salvo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

JSON_ENTRADA = os.path.join(BASE_DIR, 'questoes_para_prisma.json')
JSON_SAIDA = os.path.join(BASE_DIR, 'questoes_formatadas_llm.json')
ENV_PATH = os.path.join(os.path.dirname(BASE_DIR), '.env') # Procura o .env na raiz do projeto

load_dotenv(ENV_PATH)

client = OpenAI(
    api_key=os.getenv("MARITACA_API_KEY"),
    base_url="https://chat.maritaca.ai/api/v1"
)

def solicitar_correcao_latex(texto):
    if not texto or len(texto.strip()) < 3:
        return texto

    prompt = (r"""
        Você é um especialista em LaTeX acadêmico. 
        Sua tarefa é converter termos matemáticos, unidades de medida e fórmulas 
        presentes no texto abaixo para o formato LaTeX (entre $ para inline ou $$ para blocos). 
        Mantenha o texto original inalterado, apenas envolva ou formate o que for técnico. 
        Exemplos: 40 km/h -> $40 \text{ km/h}$, y = 363e0,03x -> $y = 363e^{0,03x}$, 1/2 -> $\frac{1}{2}$.
        Exemplos: R$40 -> $\text{R\$}40$, y = 363e0,03x -> $y = 363e^{0,03x}$, 1/2 -> $\frac{1}{2}$.
        Se for usar tabela, coloque essa formatação:
        $$
        \begin{array}{|c|c|}
        \hline
        \text{coluna} & \text{coluna} \\
        \hline
        numero & numero \\
        \hline
        \end{array}
        $$"""
        f"Texto: {texto}\n\n"
        "Retorne apenas o texto formatado, sem explicações."
    )

    try:
        response = client.chat.completions.create(
            model="sabia-3",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Erro na API: {e}")
        return texto



def processar():
    # Verifica se o arquivo de entrada existe antes de abrir
    if not os.path.exists(JSON_ENTRADA):
        print(f"ERRO: Arquivo não encontrado em: {JSON_ENTRADA}")
        return

    with open(JSON_ENTRADA, 'r', encoding='utf-8') as f:
        questoes = json.load(f)

    total = len(questoes)
    questoes_formatadas = []

    for i, q in enumerate(questoes, 1):
        print(f"[{i}/{total}] Processando: {q.get('id_externo')}")
        
        nova_q = q.copy()

        # 1. Formata Contexto
        nova_q["contexto"] = solicitar_correcao_latex(q.get("contexto"))
        
        # 2. Formata Introdução
        if q.get("introducao_alternativas"):
            nova_q["introducao_alternativas"] = solicitar_correcao_latex(q.get("introducao_alternativas"))

        # 3. Formata Alternativas
        novas_alts = []
        for alt in q.get("alternativas", []):
            nova_alt = alt.copy()
            nova_alt["texto"] = solicitar_correcao_latex(alt.get("texto"))
            novas_alts.append(nova_alt)
        
        nova_q["alternativas"] = novas_alts
        questoes_formatadas.append(nova_q)

        # Salvamento incremental
        if i % 5 == 0:
            with open(JSON_SAIDA, 'w', encoding='utf-8') as f:
                json.dump(questoes_formatadas, f, indent=4, ensure_ascii=False)

    # Salvamento final
    with open(JSON_SAIDA, 'w', encoding='utf-8') as f:
        json.dump(questoes_formatadas, f, indent=4, ensure_ascii=False)
    
    print(f"\nProcessamento concluído! Arquivo salvo em: {JSON_SAIDA}")

if __name__ == "__main__":
    processar()