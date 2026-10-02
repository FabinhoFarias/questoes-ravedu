import json
import os
import re

# --- CONFIGURAÇÃO DE CAMINHOS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# O script lerá o seu JSON final e gerará uma versão limpa
ARQUIVO_INPUT = os.path.join(BASE_DIR, 'questoes_final_ajustado.json')
ARQUIVO_OUTPUT = os.path.join(BASE_DIR, 'questoes_final_limpo.json')

def limpar_contexto_markdown():
    print(f"-> Analisando links em: {ARQUIVO_INPUT}")
    
    if not os.path.exists(ARQUIVO_INPUT):
        print(f"Erro: O arquivo {ARQUIVO_INPUT} não foi encontrado.")
        return

    try:
        with open(ARQUIVO_INPUT, 'r', encoding='utf-8') as f:
            questoes = json.load(f)

        total_substituicoes = 0

        for questao in questoes:
            contexto = questao.get("contexto", "")
            
            if contexto:
                # Regex específica para o formato Markdown: ![](url)
                # Ela identifica o padrão exato que você enviou no exemplo
                padrao_markdown = r'!\[\]\(https?://.*?\)'
                
                # Encontra todas as ocorrências na ordem em que aparecem no texto
                matches = re.findall(padrao_markdown, contexto)
                
                for idx, match in enumerate(matches):
                    # Substitui pela tag indexada (IMAGEM_0, IMAGEM_1, etc)
                    # Isso casa com a ordem da sua lista "arquivos"
                    marcador = f"[IMAGEM_{idx}]"
                    contexto = contexto.replace(match, marcador)
                    total_substituicoes += 1
                
                questao["contexto"] = contexto

        # Salva o resultado final
        with open(ARQUIVO_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(questoes, f, indent=4, ensure_ascii=False)

        print("-" * 30)
        print("LIMPEZA CONCLUÍDA")
        print(f"Total de links convertidos para tags: {total_substituicoes}")
        print(f"Arquivo gerado: {ARQUIVO_OUTPUT}")

    except Exception as e:
        print(f"Erro ao processar as expressões regulares: {e}")

if __name__ == "__main__":
    limpar_contexto_markdown()