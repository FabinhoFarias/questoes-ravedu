import json
import time
import csv
from pathlib import Path
from collections import Counter

# Mapeamento do diretório relativo ao local do script
DIRETORIO_SCRIPT = Path(__file__).resolve().parent
PASTA_BANCAS = DIRETORIO_SCRIPT / "questoes_por_banca"


def extrair_lista_cargos(questao: dict) -> list:
    """
    Extrai e normaliza todos os cargos associados à questão,
    suportando textos simples, dicionários e listas aninhadas.
    """
    raw = questao.get("_cargo_prova") or questao.get("cargos") or questao.get("cargo_nome") or questao.get("funcao")
    if not raw:
        return ["Não informado"]

    cargos_encontrados = []

    def processar_item(item):
        if not item:
            return
        if isinstance(item, dict):
            nome = item.get("nome") or item.get("descricao") or item.get("title") or item.get("sigla")
            if nome:
                cargos_encontrados.append(str(nome).strip())
        elif isinstance(item, (str, int, float)):
            texto = str(item).strip()
            if texto:
                cargos_encontrados.append(texto)

    if isinstance(raw, list):
        for sub in raw:
            processar_item(sub)
    else:
        processar_item(raw)

    return cargos_encontrados if cargos_encontrados else ["Não informado"]


def selecionar_arquivo_banca() -> Path:
    """Seleção interativa do arquivo da banca dentro de 'questoes_por_banca'."""
    if not PASTA_BANCAS.exists():
        print(f"❌ Pasta de bancas não encontrada em: {PASTA_BANCAS}")
        fallback = DIRETORIO_SCRIPT / "questoes_brutas.jsonl"
        return fallback if fallback.exists() else None

    arquivos = sorted(list(PASTA_BANCAS.glob("*.jsonl")), key=lambda p: p.stat().st_size, reverse=True)

    if not arquivos:
        print(f"⚠️ Nenhum arquivo .jsonl encontrado em: {PASTA_BANCAS}")
        return None

    print("\n==================================================")
    print("📁 SELEÇÃO DE BANCA PARA ANÁLISE DE CARGOS")
    print("==================================================")
    print("Top 10 Maiores Bancas Encontradas:\n")

    for idx, arq in enumerate(arquivos[:10], 1):
        tamanho_mb = arq.stat().st_size / (1024 * 1024)
        print(f"  [{idx:2d}] {arq.stem:<25} ({tamanho_mb:.1f} MB)")

    print("\n💡 Digite o NÚMERO, NOME da banca (ex: 'quadrix'), ou ENTER para a #1.")
    escolha = input("👉 Escolha: ").strip().lower()

    if not escolha:
        return arquivos[0]

    if escolha.isdigit():
        idx_num = int(escolha)
        if 1 <= idx_num <= len(arquivos):
            return arquivos[idx_num - 1]

    correspondencias = [arq for arq in arquivos if escolha in arq.stem.lower()]
    if correspondencias:
        if len(correspondencias) == 1:
            return correspondencias[0]

        print(f"\n🔍 {len(correspondencias)} bancas encontradas para '{escolha}':")
        for i, c in enumerate(correspondencias[:10], 1):
            tam_mb = c.stat().st_size / (1024 * 1024)
            print(f"  [{i}] {c.stem:<25} ({tam_mb:.1f} MB)")

        sub_esc = input("👉 Escolha o número da busca acima: ").strip()
        if sub_esc.isdigit() and 1 <= int(sub_esc) <= len(correspondencias):
            return correspondencias[int(sub_esc) - 1]
        return correspondencias[0]

    return arquivos[0]


def analisar_estatisticas_cargos(caminho_arquivo: Path):
    if not caminho_arquivo or not caminho_arquivo.exists():
        print(f"❌ Arquivo inválido ou inexistente: {caminho_arquivo}")
        return

    tamanho_mb = caminho_arquivo.stat().st_size / (1024 * 1024)
    print(f"\n==================================================")
    print(f"👔 ANÁLISE DE CARGOS - BANCA: {caminho_arquivo.stem.upper()}")
    print(f"📂 Arquivo: {caminho_arquivo.name} ({tamanho_mb:.2f} MB)")
    print(f"==================================================\n")

    inicio = time.time()
    total_questoes = 0
    questoes_com_cargo = 0
    cargos_counter = Counter()

    # Leitura em streaming
    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        for linha in f:
            linha_str = linha.strip()
            if not linha_str:
                continue

            try:
                q = json.loads(linha_str)
            except Exception:
                continue

            total_questoes += 1
            cargos_extraidos = extrair_lista_cargos(q)

            has_valid_cargo = False
            for cargo in cargos_extraidos:
                cargos_counter[cargo] += 1
                if cargo != "Não informado":
                    has_valid_cargo = True

            if has_valid_cargo:
                questoes_com_cargo += 1

    tempo_dec = time.time() - inicio
    qps = total_questoes / tempo_dec if tempo_dec > 0 else 0

    cargos_unicos = [c for c in cargos_counter.keys() if c != "Não informado"]
    pct_cobertura = (questoes_com_cargo / total_questoes * 100) if total_questoes > 0 else 0

    print(f"✅ Leitura concluída em {tempo_dec:.2f}s ({qps:.0f} quest/s)")
    print(f"📊 Total de Questões: {total_questoes:,}")
    print(f"🎯 Questões com Cargo Identificado: {questoes_com_cargo:,} ({pct_cobertura:.1f}%)")
    print(f"🏷️  Cargos Únicos Identificados: {len(cargos_unicos):,}\n")

    # Ordena todos os cargos por frequência
    lista_ordenada = cargos_counter.most_common()

    # Exibe resumo do Top 15
    print("--------------------------------------------------")
    print("🏆 TOP 15 CARGOS COM MAIS QUESTÕES")
    print("--------------------------------------------------")
    for idx, (cargo, qtd) in enumerate(lista_ordenada[:15], 1):
        pct = (qtd / total_questoes) * 100
        print(f" {idx:2d}. {cargo:<50} -> {qtd:>6,} questões ({pct:>5.1f}%)")

    # Menu de interação para explorar TODOS os cargos
    while True:
        print("\n==================================================")
        print("🔍 OPÇÕES DE VISUALIZAÇÃO DE TODOS OS CARGOS")
        print("==================================================")
        print("  [1] Listar TODOS os cargos da banca no terminal")
        print("  [2] Buscar/Filtrar cargos por palavra-chave (ex: Analista)")
        print("  [3] Exportar relatório completo de cargos para CSV")
        print("  [0] Sair")

        opcao = input("\n👉 Escolha uma opção: ").strip()

        if opcao == "1":
            print(f"\n📋 LISTA COMPLETA DE TODOS OS {len(lista_ordenada)} CARGOS:\n")
            print(f"{'#':<5} | {'NOME DO CARGO':<60} | {'QUESTÕES':<10} | {'% TOTAL':<8}")
            print("-" * 90)
            for i, (cargo, qtd) in enumerate(lista_ordenada, 1):
                pct = (qtd / total_questoes) * 100
                print(f"{i:<5} | {cargo:<60} | {qtd:<10,} | {pct:.2f}%")

        elif opcao == "2":
            termo = input("\n🔎 Digite o termo para filtrar (ex: 'Analista', 'Direito', 'Técnico'): ").strip().lower()
            if termo:
                filtrados = [(c, q) for c, q in lista_ordenada if termo in c.lower()]
                print(f"\n🔍 {len(filtrados)} cargos encontrados para o termo '{termo}':\n")
                print(f"{'#':<5} | {'NOME DO CARGO':<60} | {'QUESTÕES':<10} | {'% TOTAL':<8}")
                print("-" * 90)
                subtotal_qtd = 0
                for i, (cargo, qtd) in enumerate(filtrados, 1):
                    pct = (qtd / total_questoes) * 100
                    subtotal_qtd += qtd
                    print(f"{i:<5} | {cargo:<60} | {qtd:<10,} | {pct:.2f}%")
                
                pct_sub = (subtotal_qtd / total_questoes) * 100
                print("-" * 90)
                print(f"📊 SUBTOTAL DO FILTRO: {subtotal_qtd:,} questões ({pct_sub:.1f}% do total da banca)")

        elif opcao == "3":
            nome_csv = DIRETORIO_SCRIPT / f"cargos_{caminho_arquivo.stem}.csv"
            with open(nome_csv, "w", newline="", encoding="utf-8-sig") as f_csv:
                writer = csv.writer(f_csv, delimiter=";")
                writer.writerow(["Posição", "Nome do Cargo", "Quantidade de Questões", "Porcentagem do Total"])
                for i, (cargo, qtd) in enumerate(lista_ordenada, 1):
                    pct = (qtd / total_questoes) * 100
                    writer.writerow([i, cargo, qtd, f"{pct:.2f}%"])

            print(f"\n✅ Relatório exportado com sucesso!")
            print(f"📁 Arquivo gerado: {nome_csv}")

        elif opcao == "0":
            print("\nEncerrando visualização de cargos.")
            break


if __name__ == "__main__":
    arquivo_alvo = selecionar_arquivo_banca()
    if arquivo_alvo:
        analisar_estatisticas_cargos(arquivo_alvo)