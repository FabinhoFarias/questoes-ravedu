import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

arquivo_lock = Lock()

URL_API = "https://api.mapadaprova.com.br/api/question/list"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.mapadaprova.com.br/"
}

# IDs das bancas que você JÁ baixou (serão ignoradas)
BANCAS_JA_BAIXADAS_IDS = {1, 2, 3, 10}  # 1: FCC, 2: CESPE, 3: Vunesp, 10: FGV


def extrair_lista_questoes(dados: dict) -> list:
    """Garante a extração da lista de questões independente da estrutura do JSON."""
    if not isinstance(dados, dict):
        return []

    conteudo = dados.get("questoes") or dados.get("data") or dados.get("items")
    if isinstance(conteudo, dict):
        conteudo = conteudo.get("data") or conteudo.get("items") or []

    return conteudo if isinstance(conteudo, list) else []


def extrair_nome_banca(dados: dict, id_banca: int) -> str:
    """Tenta extrair o nome legível da banca a partir do retorno da API."""
    questoes = extrair_lista_questoes(dados)
    if questoes and isinstance(questoes[0], dict):
        q = questoes[0]
        banca_info = q.get("banca")
        if isinstance(banca_info, dict) and banca_info.get("nome"):
            return banca_info["nome"]
        elif isinstance(banca_info, str):
            return banca_info
        elif q.get("banca_nome"):
            return q["banca_nome"]

    return f"Banca_ID_{id_banca}"


def verificar_id_banca(id_banca: int):
    """Testa se um ID de banca possui questões cadastradas."""
    try:
        response = requests.get(
            URL_API,
            params={"limit": 1, "banca[]": id_banca, "p": 1},
            headers=HEADERS,
            timeout=8
        )
        if response.status_code == 200:
            dados = response.json()
            total = dados.get("total") or (dados.get("questoes", {}).get("total") if isinstance(dados.get("questoes"), dict) else 0)

            if total > 0:
                nome_banca = extrair_nome_banca(dados, id_banca)
                return id_banca, nome_banca, total
    except Exception:
        pass
    return id_banca, None, 0


def descobrir_bancas_ativas(id_inicio=1, id_fim=250, max_workers=10) -> dict:
    """Varre a faixa de IDs para encontrar todas as bancas com questões disponíveis."""
    print(f"🔍 Varrendo IDs de {id_inicio} a {id_fim} para descobrir bancas ativas...")
    bancas_encontradas = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(verificar_id_banca, b_id) for b_id in range(id_inicio, id_fim + 1)]

        for future in as_completed(futures):
            b_id, nome, total = future.result()
            if nome and total > 0:
                bancas_encontradas[b_id] = {"nome": nome, "total": total}

    print(f"✅ Varredura concluída! {len(bancas_encontradas)} bancas ativas encontradas no sistema.\n")
    return bancas_encontradas


def baixar_pagina(id_banca: int, pagina: int, limite_por_pagina: int, max_retries=5):
    params = {
        "limit": limite_por_pagina,
        "banca[]": id_banca,
        "instituicao[]": "",
        "resumoQuestao": "",
        "_categorizada_em_folha": "",
        "comentada": "",
        "questao_id": "",
        "filtro_data": "",
        "inicio": "",
        "fim": "",
        "status": "",
        "anulada": "",
        "p": pagina
    }

    tempo_espera = 4
    for tentativa in range(1, max_retries + 1):
        try:
            response = requests.get(URL_API, params=params, headers=HEADERS, timeout=15)

            if response.status_code == 200:
                dados = response.json()
                questoes = extrair_lista_questoes(dados)
                return pagina, questoes

            elif response.status_code == 429:
                print(f"⚠️ [Pág {pagina}] Rate limit 429. Aguardando {tempo_espera}s...")
                time.sleep(tempo_espera)
                tempo_espera *= 2

            else:
                print(f"❌ [Pág {pagina}] Erro HTTP {response.status_code}. Re-tentando em 3s...")
                time.sleep(3)

        except Exception as e:
            print(f"⚠️ [Pág {pagina}] Erro na conexão: {e}. Re-tentando em 3s...")
            time.sleep(3)

    return pagina, []


def raspar_banca_paralelo(nome_banca: str, id_banca: int, arquivo_saida: str, max_workers=5, limite_por_pagina=50):
    print(f"\n==================================================")
    print(f"📌 Processando Banca: {nome_banca} (ID: {id_banca}) em PARALELO")
    print(f"==================================================")

    res_meta = requests.get(URL_API, params={"limit": limite_por_pagina, "banca[]": id_banca, "p": 1}, headers=HEADERS)
    total_paginas = 1
    total_itens = 0

    if res_meta.status_code == 200:
        meta_json = res_meta.json()
        total_paginas = meta_json.get("last_page") or (meta_json.get("questoes", {}).get("last_page") if isinstance(meta_json.get("questoes"), dict) else 1)
        total_itens = meta_json.get("total") or (meta_json.get("questoes", {}).get("total") if isinstance(meta_json.get("questoes"), dict) else 0)

    if total_itens == 0:
        print(f"ℹ️ Nenhuma questão disponível para {nome_banca}. Pulando...")
        return

    print(f"📊 Total estimado: {total_itens} questões em {total_paginas} páginas para {nome_banca}.")
    print(f"🚀 Disparando pool de {max_workers} threads simultâneas...\n")

    with ThreadPoolExecutor(max_workers=max_workers) as executor, open(arquivo_saida, "a", encoding="utf-8") as f_out:
        futures = {
            executor.submit(baixar_pagina, id_banca, p, limite_por_pagina): p
            for p in range(1, total_paginas + 1)
        }

        concluidas = 0
        questoes_banca_salvas = 0

        for future in as_completed(futures):
            p, questoes = future.result()
            concluidas += 1

            if questoes:
                validas = []
                for q in questoes:
                    if isinstance(q, dict):
                        q["_meta_banca_nome"] = nome_banca
                        validas.append(q)

                if validas:
                    with arquivo_lock:
                        for q in validas:
                            f_out.write(json.dumps(q, ensure_ascii=False) + "\n")
                        f_out.flush()

                    questoes_banca_salvas += len(validas)
                    print(f"✅ [{nome_banca}] Progresso: {concluidas}/{total_paginas} páginas | Pág {p}: +{len(validas)} questões (Total Salvo: {questoes_banca_salvas})")


if __name__ == "__main__":
    ARQUIVO_SAIDA = "questoes_brutas.jsonl"
    MAX_WORKERS = 5

    # 1. Varre os IDs de 1 a 250 para identificar as bancas cadastradas
    todas_bancas = descobrir_bancas_ativas(id_inicio=1, id_fim=250, max_workers=10)

    # 2. Filtra apenas os IDs das bancas FALTANTES
    bancas_faltantes = {
        id_b: info
        for id_b, info in todas_bancas.items()
        if id_b not in BANCAS_JA_BAIXADAS_IDS
    }

    print(f"📋 Total de bancas pendentes para baixar: {len(bancas_faltantes)}")

    # 3. Baixa todas as bancas restantes
    for id_banca, info in sorted(bancas_faltantes.items(), key=lambda x: x[1]["total"], reverse=True):
        raspar_banca_paralelo(
            nome_banca=info["nome"],
            id_banca=id_banca,
            arquivo_saida=ARQUIVO_SAIDA,
            max_workers=MAX_WORKERS,
            limite_por_pagina=50
        )

    print(f"\n🎉 Download finalizado! Todas as questões faltantes foram salvas em '{ARQUIVO_SAIDA}'.")