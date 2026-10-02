import json
from collections import Counter
import os

def obter_caminho_irmao(nome_arquivo: str) -> str:
    """Retorna o caminho absoluto do arquivo no mesmo diretório do script."""
    if "__file__" in globals():
        diretorio_script = os.path.dirname(os.path.abspath(__file__))
    else:
        diretorio_script = os.getcwd()
    return os.path.join(diretorio_script, nome_arquivo)


def analisar_base_questoes(caminho_arquivo: str, top_n=15):
    if not os.path.exists(caminho_arquivo):
        print(f"❌ Arquivo não encontrado no caminho esperado:")
        print(f"   👉 {caminho_arquivo}")
        return

    print(f"🔍 Arquivo localizado com sucesso!")
    print(f"📂 Caminho: {caminho_arquivo}")
    print("⏳ Processando as 550 mil questões em streaming...\n")

    total_questoes = 0
    bancas_count = Counter()
    cargos_count = Counter()
    areas_cargo_count = Counter()
    disciplinas_count = Counter()
    orgaos_count = Counter()
    assuntos_count = Counter()
    anos_count = Counter()

    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue

            try:
                q = json.loads(linha)
            except json.JSONDecodeError:
                continue

            total_questoes += 1

            # 1. Banca (_meta_banca_nome ou banca)
            banca = q.get("_meta_banca_nome") or q.get("banca") or "Não informado"
            if isinstance(banca, dict):
                banca = banca.get("nome") or banca.get("sigla") or "Outros"
            bancas_count[str(banca)] += 1

            # 2. Cargo (Chave exata: _cargo_prova)
            cargo = q.get("_cargo_prova") or "Não informado"
            if isinstance(cargo, dict):
                cargo = cargo.get("nome", "Outros")
            cargos_count[str(cargo)] += 1

            # 3. Área do Cargo (Chave exata: area_cargo)
            area = q.get("area_cargo") or "Não informado"
            if isinstance(area, dict):
                area = area.get("nome", "Outros")
            areas_cargo_count[str(area)] += 1

            # 4. Disciplina / Matéria (Chave exata: _nome_disciplina)
            disciplina = q.get("_nome_disciplina") or "Não informado"
            if isinstance(disciplina, dict):
                disciplina = disciplina.get("nome", "Outros")
            disciplinas_count[str(disciplina)] += 1

            # 5. Órgão (Chave exata: _orgao_prova)
            orgao = q.get("_orgao_prova") or "Não informado"
            if isinstance(orgao, dict):
                orgao = orgao.get("nome", "Outros")
            orgaos_count[str(orgao)] += 1

            # 6. Assuntos (Chaves exatas: assunto_nome ou assuntos_nome)
            assunto = q.get("assunto_nome") or q.get("assuntos_nome") or "Não informado"
            if isinstance(assunto, list):
                for a in assunto:
                    a_nome = a.get("nome") if isinstance(a, dict) else str(a)
                    assuntos_count[a_nome] += 1
            elif isinstance(assunto, dict):
                assuntos_count[assunto.get("nome", "Outros")] += 1
            else:
                assuntos_count[str(assunto)] += 1

            # 7. Ano da Prova (Chave exata: ano_prova)
            ano = q.get("ano_prova") or "Não informado"
            anos_count[str(ano)] += 1

            if total_questoes % 50000 == 0:
                print(f"  ... {total_questoes:,} questões lidas")

    print("\n" + "="*60)
    print("📊 RELATÓRIO CORRIGIDO DA BASE DE QUESTÕES")
    print("="*60)
    print(f"📦 Total Geral de Questões Analisadas: {total_questoes:,}")

    def exibir_top(titulo, contador, n=top_n):
        print(f"\n--- 🏆 Top {n} {titulo} ---")
        for item, count in contador.most_common(n):
            perc = (count / total_questoes) * 100 if total_questoes > 0 else 0
            print(f"  • {item}: {count:,} ({perc:.1f}%)")

    exibir_top("Bancas", bancas_count)
    exibir_top("Disciplinas / Matérias", disciplinas_count)
    exibir_top("Assuntos Principais", assuntos_count)
    exibir_top("Cargos", cargos_count)
    exibir_top("Áreas dos Cargos", areas_cargo_count)
    exibir_top("Órgãos das Provas", orgaos_count)
    exibir_top("Anos das Provas", anos_count)

    # Exporta relatório resumido leve em JSON
    relatorio = {
        "total_questoes": total_questoes,
        "top_bancas": dict(bancas_count.most_common(50)),
        "top_disciplinas": dict(disciplinas_count.most_common(50)),
        "top_assuntos": dict(assuntos_count.most_common(50)),
        "top_cargos": dict(cargos_count.most_common(50)),
        "top_areas_cargo": dict(areas_cargo_count.most_common(50)),
        "top_orgaos": dict(orgaos_count.most_common(50)),
        "top_anos": dict(anos_count.most_common(50))
    }

    arquivo_relatorio = obter_caminho_irmao("relatorio_estatisticas_questoes.json")
    with open(arquivo_relatorio, "w", encoding="utf-8") as f_rel:
        json.dump(relatorio, f_rel, indent=4, ensure_ascii=False)

    print(f"\n💾 Relatório corrigido salvo em:\n👉 {arquivo_relatorio}")


if __name__ == "__main__":
    NOME_ARQUIVO_JSONL = "questoes_brutas.jsonl"
    caminho_absoluto = obter_caminho_irmao(NOME_ARQUIVO_JSONL)
    analisar_base_questoes(caminho_absoluto, top_n=15)