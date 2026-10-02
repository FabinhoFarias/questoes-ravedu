import json
import os

def excluir_ultimas_100_questoes():
    # Encontra a pasta do script e o caminho do arquivo final
    pasta_do_script = os.path.dirname(os.path.abspath(__file__))
    caminho_saida = os.path.join(pasta_do_script, 'questoes_prontas.json')

    # 1. Verifica se o arquivo realmente existe
    if not os.path.exists(caminho_saida):
        print("⚠️ Erro: O arquivo 'questoes_prontas.json' não foi encontrado nesta pasta.")
        return

    # 2. Abre o arquivo e carrega a lista atual
    with open(caminho_saida, 'r', encoding='utf-8') as f:
        lista_questoes = json.load(f)

    total_atual = len(lista_questoes)

    # 3. Verifica se o arquivo tem questões suficientes para remover
    if total_atual == 0:
        print("⚠️ O arquivo já está completamente vazio.")
        return
    
    if total_atual <= 100:
        # Se tiver 100 ou menos, limpa o arquivo inteiro
        lista_questoes = []
        print(f"🗑️ O arquivo tinha {total_atual} questões (menos de 100). Todas foram removidas.")
    else:
        # Fatiamento Python: remove os últimos 100 elementos
        lista_questoes = lista_questoes[:-100]
        print(f"✂️ Removidas as últimas 100 questões com sucesso!")

    # 4. Salva a lista atualizada de volta no arquivo
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        json.dump(lista_questoes, f, ensure_ascii=False, indent=2)

    print(f"📉 Total restante no arquivo: {len(lista_questoes)} questões.")

# Executa a função caso o script seja chamado diretamente
if __name__ == "__main__":
    excluir_ultimas_100_questoes()