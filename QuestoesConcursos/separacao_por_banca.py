import os
import json
import time
import re
from pathlib import Path

# Define o diretório base como a pasta ONDE O SCRIPT ESTÁ SALVO
DIRETORIO_BASE = Path(__file__).resolve().parent


def sanitizar_nome_arquivo(nome: str) -> str:
    """Converte o nome da banca para um nome de arquivo seguro."""
    if not nome:
        return "banca_desconhecida"
    nome_limpo = re.sub(r'[^\w\s-]', '', nome).strip()
    nome_limpo = re.sub(r'[\s-]+', '_', nome_limpo)
    return nome_limpo.lower() or "banca_desconhecida"


def extrair_nome_banca(dado: dict) -> str:
    """Identifica o nome da banca independente da estrutura do JSON."""
    if dado.get("_meta_banca_nome"):
        return dado["_meta_banca_nome"]
    
    banca = dado.get("banca")
    if isinstance(banca, dict):
        return banca.get("nome") or banca.get("sigla") or "Desconhecida"
    elif isinstance(banca, str):
        return banca
        
    return dado.get("banca_nome") or "Desconhecida"


def separar_questoes_por_banca(caminho_input: Path, pasta_saida: Path, tamanho_buffer: int = 50000):
    """
    Lê o JSONL bruto e separa em arquivos JSONL individuais por banca.
    Utiliza caminhos do tipo Path (relativos).
    """
    if not caminho_input.exists():
        print(f"❌ Arquivo não encontrado no caminho relativo: {caminho_input}")
        return

    # Cria a pasta de saída se ela não existir
    pasta_saida.mkdir(parents=True, exist_ok=True)
    
    tamanho_gb = caminho_input.stat().st_size / (1024 ** 3)
    print(f"🚀 Iniciando separação de questões por banca...")
    print(f"📂 Arquivo de origem: {caminho_input} ({tamanho_gb:.2f} GB)")
    print(f"📁 Pasta de destino: {pasta_saida}/\n")

    buffers = {}
    questoes_por_banca_count = {}
    total_linhas = 0
    tempo_inicio = time.time()

    def descarregar_buffer(chave_banca: str):
        """Escreve o bloco acumulado da banca no disco."""
        buf = buffers[chave_banca]
        if not buf["linhas"]:
            return
        
        caminho_arquivo = pasta_saida / f"{chave_banca}.jsonl"
        
        with open(caminho_arquivo, "a", encoding="utf-8") as f_out:
            f_out.writelines(buf["linhas"])
            
        buf["linhas"].clear()

    def descarregar_todos_buffers():
        """Descarrega os acumulados de todas as bancas."""
        for chave in buffers:
            descarregar_buffer(chave)

    try:
        with open(caminho_input, "r", encoding="utf-8") as f_in:
            for linha in f_in:
                linha_str = linha.strip()
                if not linha_str:
                    continue
                
                total_linhas += 1
                
                try:
                    dado = json.loads(linha_str)
                    nome_banca = extrair_nome_banca(dado)
                except Exception:
                    nome_banca = "Erro_Parse_JSON"

                chave_banca = sanitizar_nome_arquivo(nome_banca)

                if chave_banca not in buffers:
                    buffers[chave_banca] = {
                        "nome_real": nome_banca,
                        "linhas": []
                    }
                    questoes_por_banca_count[chave_banca] = 0

                buffers[chave_banca]["linhas"].append(linha_str + "\n")
                questoes_por_banca_count[chave_banca] += 1

                if total_linhas % tamanho_buffer == 0:
                    descarregar_todos_buffers()
                    tempo_decorrido = time.time() - tempo_inicio
                    lps = total_linhas / tempo_decorrido if tempo_decorrido > 0 else 0
                    print(f"🔄 Processadas {total_linhas:,} questões ({lps:.0f} quest/s)...", end="\r")

        descarregar_todos_buffers()

    except KeyboardInterrupt:
        print("\n⚠️ Processo interrompido pelo usuário! Salvando dados acumulados...")
        descarregar_todos_buffers()
        return

    tempo_total = time.time() - tempo_inicio
    print(f"\n\n✅ Concluído em {tempo_total:.2f} segundos!")
    print(f"📊 Total de questões processadas: {total_linhas:,}")
    print(f"🏛️ Total de bancas identificadas: {len(questoes_por_banca_count)}\n")
    
    print("--- 🏆 Top 10 Bancas com Mais Questões ---")
    bancas_ordenadas = sorted(questoes_por_banca_count.items(), key=lambda x: x[1], reverse=True)
    for chave, count in bancas_ordenadas[:10]:
        nome_exibicao = buffers[chave]["nome_real"] if chave in buffers else chave
        print(f" • {nome_exibicao}: {count:,} questões -> {pasta_saida / f'{chave}.jsonl'}")


if __name__ == "__main__":
    # Caminhos configurados de forma relativa ao local do script:
    ARQUIVO_ENTRADA = DIRETORIO_BASE / "questoes_brutas_2.jsonl"
    PASTA_SAIDA = DIRETORIO_BASE / "questoes_por_banca"
    
    separar_questoes_por_banca(
        caminho_input=ARQUIVO_ENTRADA,
        pasta_saida=PASTA_SAIDA,
        tamanho_buffer=50000
    )