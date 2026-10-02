import json
import time
from pathlib import Path
from collections import Counter

# Mapeia a pasta 'QuestoesConcursos/questoes_por_banca' independente de onde o terminal for aberto
DIRETORIO_SCRIPT = Path(__file__).resolve().parent
PASTA_BANCAS = DIRETORIO_SCRIPT / "questoes_por_banca"


def sanitizar_texto(val) -> str:
    """Extrai e normaliza valores de metadados (strings, dicionários ou listas)."""
    if val is None:
        return "Não informado"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, str):
        texto = val.strip()
        return texto if texto else "Não informado"
    if isinstance(val, dict):
        return val.get("nome") or val.get("descricao") or val.get("title") or val.get("sigla") or "Não informado"
    if isinstance(val, list):
        itens = [sanitizar_texto(item) for item in val]
        itens_validos = [i for i in itens if i != "Não informado"]
        return " > ".join(itens_validos) if itens_validos else "Não informado"
    return str(val)


def selecionar_arquivo_banca() -> Path:
    """
    Localiza os arquivos na pasta 'questoes_por_banca' e permite escolher
    pelo Top 10 maiores ou buscando por parte do nome (ex: 'quadrix', 'aocp').
    """
    if not PASTA_BANCAS.exists():
        print(f"❌ Pasta de bancas não encontrada em: {PASTA_BANCAS}")
        fallback = DIRETORIO_SCRIPT / "questoes_brutas_2.jsonl"
        return fallback if fallback.exists() else None

    # Ordena todos os arquivos .jsonl do maior para o menor
    arquivos = sorted(list(PASTA_BANCAS.glob("*.jsonl")), key=lambda p: p.stat().st_size, reverse=True)

    if not arquivos:
        print(f"⚠️ Nenhum arquivo .jsonl encontrado em: {PASTA_BANCAS}")
        return None

    print("\n==================================================")
    print("📁 SELEÇÃO DE BANCA PARA ANÁLISE DE METADADOS")
    print("==================================================")
    print("Top 10 Maiores Bancas Encontradas:\n")

    for idx, arq in enumerate(arquivos[:10], 1):
        tamanho_mb = arq.stat().st_size / (1024 * 1024)
        print(f"  [{idx:2d}] {arq.stem:<25} ({tamanho_mb:.1f} MB)")

    print("\n💡 Digite o NÚMERO (ex: 1), parte do NOME da banca (ex: 'quadrix' ou 'cespe'), ou aperte ENTER para a #1.")
    escolha = input("👉 Escolha: ").strip().lower()

    if not escolha:
        return arquivos[0]

    # Escolha por número da lista principal
    if escolha.isdigit():
        idx_num = int(escolha)
        if 1 <= idx_num <= len(arquivos):
            return arquivos[idx_num - 1]

    # Busca por filtro de nome
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

    print(f"⚠️ Nenhuma banca encontrada com '{escolha}'. Selecionando a maior ({arquivos[0].stem})...")
    return arquivos[0]


def analisar_metadados_otimizado(caminho_arquivo: Path, top_n: int = 10):
    if not caminho_arquivo or not caminho_arquivo.exists():
        print(f"❌ Arquivo inválido ou inexistente: {caminho_arquivo}")
        return

    tamanho_mb = caminho_arquivo.stat().st_size / (1024 * 1024)
    print(f"\n==================================================")
    print(f"🔍 ANALISANDO BANCA: {caminho_arquivo.stem.upper()}")
    print(f"📂 Arquivo: {caminho_arquivo.name} ({tamanho_mb:.2f} MB)")
    print(f"==================================================\n")

    inicio = time.time()
    total_questoes = 0
    todas_chaves = Counter()

    # Contadores otimizados em C
    cargos = Counter()
    disciplinas = Counter()
    assuntos = Counter()
    anos = Counter()
    instituicoes = Counter()
    modalidades = Counter()

    amostra_questao = None

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

            if amostra_questao is None:
                amostra_questao = q

            # Registra a frequência de todas as chaves do JSON
            for k in q.keys():
                todas_chaves[k] += 1

            # Mapeamento rápido de campos
            cargo_val = q.get("cargo") or q.get("cargos")
            cargos[sanitizar_texto(cargo_val)] += 1

            disc_val = q.get("disciplina") or q.get("materia") or q.get("disciplina_nome")
            disciplinas[sanitizar_texto(disc_val)] += 1

            raw_assuntos = q.get("assuntos") or q.get("assunto") or q.get("topicos")
            if isinstance(raw_assuntos, list):
                for sub in raw_assuntos:
                    assuntos[sanitizar_texto(sub)] += 1
            else:
                assuntos[sanitizar_texto(raw_assuntos)] += 1

            ano_val = q.get("ano") or q.get("data")
            anos[sanitizar_texto(ano_val)] += 1

            inst_val = q.get("instituicao") or q.get("orgao") or q.get("instituicao_nome")
            instituicoes[sanitizar_texto(inst_val)] += 1

            mod_val = q.get("modalidade") or q.get("tipo") or q.get("formato")
            modalidades[sanitizar_texto(mod_val)] += 1

    tempo_dec = time.time() - inicio
    qps = total_questoes / tempo_dec if tempo_dec > 0 else 0

    print(f"✅ Análise concluída em {tempo_dec:.2f}s ({qps:.0f} questões/seg)")
    print(f"📊 Total de questões processadas: {total_questoes:,}\n")

    print("🔑 CHAVES DE METADADOS PRESENTES NO JSON:")
    for chave, count in todas_chaves.most_common():
        pct = (count / total_questoes) * 100
        print(f" • {chave:<25} -> {count:,} questões ({pct:.1f}%)")

    def exibir_top(titulo: str, contador: Counter):
        print(f"\n--- 📌 Top {top_n} {titulo} ---")
        itens = [(k, v) for k, v in contador.most_common() if k != "Não informado"]
        if not itens:
            print("  (Nenhum dado informado)")
            return
        for item, count in itens[:top_n]:
            pct = (count / total_questoes) * 100
            print(f" • {item} -> {count:,} ({pct:.1f}%)")

    exibir_top("Disciplinas / Matérias", disciplinas)
    exibir_top("Assuntos / Tópicos", assuntos)
    exibir_top("Cargos", cargos)
    exibir_top("Instituições / Órgãos", instituicoes)
    exibir_top("Anos de Prova", anos)
    exibir_top("Modalidades / Tipos de Questão", modalidades)

    print("\n==================================================")
    print("📋 EXEMPLO DE QUESTÃO COMPLETA (AMOSTRA FORMATADA)")
    print("==================================================")
    if amostra_questao:
        json_str = json.dumps(amostra_questao, ensure_ascii=False, indent=2)
        print(json_str[:2500])
        if len(json_str) > 2500:
            print("\n... [restante da questão omitido na exibição]")


if __name__ == "__main__":
    arquivo_alvo = selecionar_arquivo_banca()
    if arquivo_alvo:
        analisar_metadados_otimizado(arquivo_alvo, top_n=10)


