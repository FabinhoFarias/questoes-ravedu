api_key = "" # LEMBRAR DE OCULTAR A CHAVE EM ALGUM LUGAR E ANTES DE FAZER DEPLOY NO GIT

import os
import json
import requests
import google.generativeai as genai
import google.api_core.exceptions

prompt = """
Você é um assistente educacional responsável por ranquear e categorizar questões de matemática do ENEM com base nos seguintes critérios:
1. **Assunto:** O tema principal da questão (Ex: Números e Operações, Geometria, Álgebra, Estatística).
2. **Competência:** Número da competência envolvida, de 1 a 7.
    - Competência 1: Construir significados para os números naturais, inteiros, racionais e reais.
    - Competência 2: Utilizar o conhecimento geométrico para realizar a leitura e a representação da realidade.
    - Competência 3: Construir noções de grandezas e medidas para a compreensão da realidade.
    - Competência 4: Construir noções de variação de grandezas para a compreensão da realidade.
    - Competência 5: Modelar e resolver problemas que envolvem variáveis socioeconômicas ou técnico-científicas, usando representações algébricas.
    - Competência 6: Interpretar informações de natureza científica e social obtidas da leitura de gráficos e tabelas.
    - Competência 7: Compreender o caráter aleatório e não determinístico dos fenômenos naturais e sociais usando estatística e probabilidade.
3. **Habilidade:** Número da habilidade específica dentro da competência, de H1 a H30.
    - **Competência 1 (Números):**
      - H1: Reconhecer significados e representações dos números e operações.
      - H2: Identificar padrões numéricos ou princípios de contagem.
      - H3: Resolver problemas que envolvem conhecimentos numéricos.
      - H4: Avaliar a razoabilidade de um resultado numérico.
      - H5: Avaliar propostas de intervenção com conhecimentos numéricos.
    - **Competência 2 (Geometria):**
      - H6: Interpretar localização e movimentação de objetos no espaço tridimensional.
      - H7: Identificar características de figuras planas ou espaciais.
      - H8: Resolver problemas que envolvam conhecimentos geométricos.
      - H9: Utilizar conhecimentos geométricos na seleção de argumentos para problemas cotidianos.
    - **Competência 3 (Grandezas e Medidas):**
      - H10: Identificar relações entre grandezas e unidades de medida.
      - H11: Utilizar a noção de escalas em representações cotidianas.
      - H12: Resolver problemas envolvendo medidas de grandezas.
      - H13: Avaliar medições na construção de argumentos consistentes.
      - H14: Avaliar intervenções usando conhecimentos de grandezas e medidas.
    - **Competência 4 (Variação de Grandezas):**
      - H15: Identificar dependência entre grandezas.
      - H16: Resolver problemas de variação direta ou inversa de grandezas.
      - H17: Analisar informações de variação de grandezas para construir argumentos.
      - H18: Avaliar intervenções envolvendo variação de grandezas.
    - **Competência 5 (Álgebra):**
      - H19: Identificar representações algébricas que expressem relações entre grandezas.
      - H20: Interpretar gráficos que representem relações entre grandezas.
      - H21: Resolver problemas que envolvam modelagem algébrica.
      - H22: Utilizar conhecimentos algébricos/geométricos na construção de argumentos.
      - H23: Avaliar intervenções utilizando conhecimentos algébricos.
    - **Competência 6 (Gráficos e Tabelas):**
      - H24: Utilizar gráficos ou tabelas para fazer inferências.
      - H25: Resolver problemas com dados apresentados em gráficos ou tabelas.
      - H26: Analisar informações de gráficos ou tabelas para construção de argumentos.
    - **Competência 7 (Estatística e Probabilidade):**
      - H27: Calcular medidas de tendência central ou dispersão em dados.
      - H28: Resolver problemas que envolvam estatística e probabilidade.
      - H29: Utilizar conhecimentos de estatística e probabilidade na construção de argumentos.
      - H30: Avaliar intervenções com base em conhecimentos de estatística e probabilidade.
4. **Dificuldade:** Classifique a questão em uma das seguintes categorias de dificuldade: Facil, Medio, Dificil.
5. **InterpretaçãoContextual:** A questão exige interpretação de um contexto específico? Responda com "True" ou "False".
6. **ConsistenciaTextual:** A questão fornecida tem dados e textos que dê para ser resolvida e classificada? Caso os textos dela sejam ruins você responde "False". Responda com "True" ou "False".
Você vai retornar APENAS uma lista onde a posição 0 é o primeiro tópico até a posição 5 com o tópico 6.
Exemplo de categorização:

["Números e Operações", 1, "H3", "Medio", True, True]

Classifique a questão fornecida com base nesses critérios e retorne apenas uma lista."""





# Acessar API ENEM para gerar as questões e classificar com uma lista
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")


def adicionar_dados_json(caminho_pasta, ano_da_prova, dados_novos):
    """Função para criar uma pasta, salvar um arquivo JSON e adicionar novos dados como itens de um dicionário.
        Parâmetros:
            - caminho_pasta (str): Caminho da pasta onde o arquivo será salvo.
            - ano_da_prova (str/int): Ano da prova, utilizado para nomear o arquivo JSON.
            - dados_novos (dict): Dicionário com novos dados a serem adicionados."""
    nome_arquivo = f"Questoes_Matematica_{ano_da_prova}.json"
    # Criar a pasta se não existir
    if not os.path.exists(caminho_pasta):
        os.makedirs(caminho_pasta)
    caminho_completo = os.path.join(caminho_pasta, nome_arquivo)
    print(caminho_completo)
    # Ler os dados existentes, se o arquivo já existir
    if os.path.exists(caminho_completo):
        with open(caminho_completo, "r") as arquivo_json:
            dados_existentes = json.load(arquivo_json)
    else:
        dados_existentes = {}
    nova_chave = f"Questao_{len(dados_existentes) + 136}"
    dados_existentes[nova_chave] = dados_novos
    with open(caminho_completo, "w") as arquivo_json:
        json.dump(dados_existentes, arquivo_json, indent=4)
    print(f"Dados adicionados em {caminho_completo}")

# # Exemplo de uso:
# adicionar_dados_json("ArquivosJson", 2023, {"pergunta": "Qual é o valor de 2+2?", "resposta": 4})

# Testando a função
caminho = "ArquivosJson"
nome_arquivo = "dados_matematica.json"
dados_novos = {
    "nome": "João",
    "idade": 25,
    "profissao": "Engenheiro",
    "cidade": "São Paulo",
    "hobbies": ["leitura", "programação", "esportes"]
}

# Chamando a função para adicionar os dados
# adicionar_dados_json(caminho, nome_arquivo, dados_novos)

# # Adicionando novos dados para testar
# novos_dados = {
#     "nome": "Maria",
#     "idade": 30,
#     "profissao": "Médica",
#     "cidade": "Rio de Janeiro"
# }
# adicionar_dados_json(caminho, nome_arquivo, novos_dados)


caminho_completo = "Dados\Questoes_Matematica_2009.json"
# with open(caminho_completo, "r") as arquivo_json:
#     dados_existentes = json.load(arquivo_json)
#     print(dados_existentes)
#     if "Questao_136" in dados_existentes:
#         print("jonfijvnvjinwivlsnbfvslb v")

def Verificar_Questao(AnoDaQuestao, NumeroQuestao):
    caminho_completo = f"Dados\Questoes_Matematica_{AnoDaQuestao}.json"
    with open(caminho_completo, "r") as arquivo_json:
        dados_existentes = json.load(arquivo_json)
        if f"Questao_{NumeroQuestao}" in dados_existentes:
            return True
        else:
            return False


def Criar_Arquivo(ano):
    # Definir o caminho completo do arquivo
    caminho_completo = f"Dados/Questoes_Matematica_{ano}.json"
    
    # Verificar se o diretório "Dados" existe, caso contrário, criar o diretório
    if not os.path.exists(os.path.dirname(caminho_completo)):
        os.makedirs(os.path.dirname(caminho_completo))
    
    # Criar o arquivo JSON se ele não existir
    if not os.path.exists(caminho_completo):
        with open(caminho_completo, "w") as arquivo_json:
            json.dump({}, arquivo_json)  # Criar um JSON vazio com um dicionário vazio
        print(f"Arquivo '{caminho_completo}' criado com sucesso.")

