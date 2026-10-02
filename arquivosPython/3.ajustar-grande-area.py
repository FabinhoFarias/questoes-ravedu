import json
import os

# --- AJUSTE DE CAMINHOS AUTOMÁTICO ---
# Pega o caminho absoluto da pasta onde este script (.py) está
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define os caminhos baseados na localização do script
ARQUIVO_INPUT = os.path.join(BASE_DIR, 'questoes_formatadas_llm.json')
ARQUIVO_OUTPUT = os.path.join(BASE_DIR, 'questoes_final_ajustado.json')

def ajustar_capitalizacao():
    print(f"-> Procurando arquivo em: {ARQUIVO_INPUT}")
    
    if not os.path.exists(ARQUIVO_INPUT):
        print(f"Erro: O arquivo não foi encontrado na pasta {BASE_DIR}")
        return

    try:
        with open(ARQUIVO_INPUT, 'r', encoding='utf-8') as f:
            questoes = json.load(f)

        alterados = 0
        index = 0
        for questao in questoes:
            # Verifica se a chave existe e se é o valor antigo
            if questao["grande_area"]:
                questao["grande_area"] = "Linguagens"
                alterados += 1
            if questao["disciplina"]:
                antigo = questao["disciplina"]
                questao["disciplina"] = "figuras de linguagem"
                print(f"Mudando o index {index} de {antigo} para {questao["disciplina"]}")
            index += 1

        with open(ARQUIVO_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(questoes, f, indent=4, ensure_ascii=False)

        print("-" * 30)
        print(f"Sucesso!")
        print(f"Total de questões: {len(questoes)}")
        print(f"Alterações feitas: {alterados}")
        print(f"Novo arquivo: {ARQUIVO_OUTPUT}")

    except Exception as e:
        print(f"Erro ao processar: {e}")

if __name__ == "__main__":
    ajustar_capitalizacao()