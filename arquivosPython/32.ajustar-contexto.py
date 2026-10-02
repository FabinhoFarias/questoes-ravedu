import re
import shutil
import os
import json
from PIL import Image

# --- CONFIGURAÇÃO ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

grande_area_atual = "Matematica"
disciplina_atual = "interpretacaodetexto"

PASTA_QUESTOES_RAIZ = os.path.join(BASE_DIR, 'Questoes', grande_area_atual.upper(), "loteEnem33", "imagensQuestoes")
# print(PASTA_QUESTOES_RAIZ)
PREFIXO_PASTA = "loteEnem"
LOTE_INICIAL = 1
TOTAL_LOTES_PARA_PROCESSAR = 20  # Quantas pastas à frente deseja tratar (ex: 27, 28, 29...)

def separar_contexto_local():
    for i in range(TOTAL_LOTES_PARA_PROCESSAR):
        num_lote = LOTE_INICIAL + i
        nome_lote = f"{PREFIXO_PASTA}{num_lote}"
        caminho_json = os.path.join(PASTA_QUESTOES_RAIZ, nome_lote, f"questoes_{PREFIXO_PASTA}{num_lote}.json")
        print(caminho_json)

        if not os.path.exists(caminho_json):
            print(f"⚠️ Arquivo não encontrado: {caminho_json}")
            continue

        with open(caminho_json, 'r', encoding='utf-8') as f:
            questoes = json.load(f)

        alterado = False
        for q in questoes:
            intro = q.get("introducao_alternativas", "").strip()
            
            if "." in intro:
                partes = intro.rsplit(".", 1)
                primeira_parte = partes[0].strip() + "."
                segunda_parte = partes[1].strip()

                if segunda_parte: 
                    if "IMAGEM" in segunda_parte:
                        expr = segunda_parte.split("]")[0].split("[")[1]
                        primeira_parte = f"{primeira_parte} [{expr}]"
                        segunda_parte = segunda_parte.split(f"[{expr}]")
                        segunda_parte = segunda_parte[-1].lstrip()
                        if '' not in segunda_parte:
                            primeira_parte = f"{primeira_parte} {segunda_parte[0]}"
                            pass

                        # print(f"{primeira_parte} \n {segunda_parte} \n" )
                    q["contexto"] = f"{primeira_parte}".strip()
                    q["introducao_alternativas"] = segunda_parte
                    alterado = True

        if alterado:
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(questoes, f, indent=2, ensure_ascii=False)
            print(f"✅ {nome_lote.upper()} reorganizado com sucesso!")
        else:
            print(f"ℹ️ {nome_lote.upper()} não precisou de alterações.")

def ajustar_titulo_e_ano():
    for i in range(TOTAL_LOTES_PARA_PROCESSAR):
        num_lote = LOTE_INICIAL + i
        nome_lote = f"{PREFIXO_PASTA}{num_lote}"
        caminho_json = os.path.join(PASTA_QUESTOES_RAIZ, nome_lote, f"questoes_{PREFIXO_PASTA}{num_lote}.json")

        if not os.path.exists(caminho_json):
            print(f"⚠️ Arquivo não encontrado: {caminho_json}")
            continue

        with open(caminho_json, 'r', encoding='utf-8') as f:
            questoes = json.load(f)

        alterado = False
        for q in questoes:
            titulo_original = q.get("title", "")
            
            # Regex que encontra um hífen seguido do ano (ex: " - ENEM 2013" ou " - ENEM 2013 Segunda Aplicação")
            # Captura o ano em um grupo de quatro dígitos (\d{4})
            match = re.search(r'-\s*(.*?)\s+(\d{4})', titulo_original)
            
            if match:
                banca = match.group(1).strip()  # Ex: "ENEM"
                # Reconstrói o título parando na banca e removendo o ano
                # Ex de resultado: "Questão M0424 - ENEM"
                prefixo_questao = titulo_original.split("-")[0].strip()
                q["title"] = f"{prefixo_questao} - {banca}"
                
                # Seta o ano para None (que vira null no JSON)
                q["ano"] = None  # Se preferir string vazia, troque por ""
                alterado = True

        if alterado:
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(questoes, f, indent=2, ensure_ascii=False)
            print(f"✅ {nome_lote.upper()} - Títulos e anos limpos com sucesso!")
        else:
            print(f"ℹ️ {nome_lote.upper()} - Nenhuma alteração de título necessária.")

def alterar_grande_area_natureza():
    """
    Percorre os lotes e altera/adiciona o campo da grande área para 'Natureza'.
    Ajuste a chave 'grande_area' caso o seu banco utilize outro nome (ex: 'materia').
    """
    for i in range(TOTAL_LOTES_PARA_PROCESSAR):
        num_lote = LOTE_INICIAL + i
        nome_lote = f"{PREFIXO_PASTA}{num_lote}"
        caminho_json = os.path.join(PASTA_QUESTOES_RAIZ, nome_lote, f"questoes_{PREFIXO_PASTA}{num_lote}.json")

        if not os.path.exists(caminho_json):
            continue

        with open(caminho_json, 'r', encoding='utf-8') as f:
            questoes = json.load(f)

        alterado = False
        for q in questoes:
            # Verifica se já é "Natureza" para evitar reescrita desnecessária
            if q.get("grande_area") != "Natureza":
                q["grande_area"] = "Natureza"
                alterado = True

        if alterado:
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(questoes, f, indent=2, ensure_ascii=False)
            print(f"✅ {nome_lote.upper()} - Grande área alterada para 'Natureza' com sucesso!")
        else:
            print(f"ℹ️ {nome_lote.upper()} - Grande área já estava configurada como 'Natureza'.")

def comprimir_imagens_generalista(caminho_pasta, qualidade_jpg=75, cores_png=256):
    """
    Percorre a pasta e aplica a melhor estratégia de compressão por formato.
    Corrigido o bug de quantização para imagens PNG em modo RGBA (transparência).
    """
    extensoes_validas = ('.jpg', '.jpeg', '.png', '.webp')
    
    if not os.path.exists(caminho_pasta):
        print(f"❌ O caminho especificado não existe: {caminho_pasta}")
        return

    print(f"⚡ Iniciando compressão inteligente em: {caminho_pasta}\n" + "-"*50)
    contagem_processados = 0

    for raiz, _, arquivos in os.walk(caminho_pasta):
        for arquivo in arquivos:
            if arquivo.lower().endswith(extensoes_validas):
                caminho_completo = os.path.join(raiz, arquivo)
                
                try:
                    tamanho_original = os.path.getsize(caminho_completo)
                    
                    with Image.open(caminho_completo) as img:
                        formato = img.format
                        
                        # 1. Estratégia para PNG (Tratando RGB e RGBA separadamente para evitar erros)
                        if formato == 'PNG':
                            if img.mode == 'RGBA':
                                # FASTOCTREE (method=2) é obrigatório para imagens com transparência
                                img_otimizada = img.quantize(colors=cores_png, method=Image.Quantize.FASTOCTREE)
                            elif img.mode == 'RGB':
                                # MAXCOVERAGE funciona perfeitamente para imagens sem transparência
                                img_otimizada = img.quantize(colors=cores_png, method=Image.Quantize.MAXCOVERAGE)
                            else:
                                # Caso seja outro modo menor (ex: P ou L), mantém como está
                                img_otimizada = img
                                
                            img_otimizada.save(caminho_completo, format=formato, optimize=True)
                        
                        # 2. Estratégia para JPEG / WEBP
                        elif formato in ('JPEG', 'JPG', 'WEBP'):
                            if img.mode in ('RGBA', 'LA'):
                                img = img.convert('RGB')
                            img.save(caminho_completo, format=formato, optimize=True, quality=qualidade_jpg)
                        
                        # 3. Fallback
                        else:
                            img.save(caminho_completo, format=formato, optimize=True)
                    
                    # Cálculo do ganho de espaço
                    tamanho_final = os.path.getsize(caminho_completo)
                    if tamanho_original > 0:
                        reducao = ((tamanho_original - tamanho_final) / tamanho_original) * 100
                        
                        if reducao > 0.5:
                            print(f"✅ [{formato}] {arquivo} -> Reduzido em {reducao:.1f}%")
                        else:
                            print(f"ℹ️ [{formato}] {arquivo} -> Já estava no tamanho mínimo ideal.")
                    
                    contagem_processados += 1
                    
                except Exception as e:
                    print(f"❌ Erro ao processar {arquivo}: {str(e)}")

    print("-"*50 + f"\n🎉 Processo concluído! {contagem_processados} imagens analisadas.")

if __name__ == "__main__":
    comprimir_imagens_generalista(PASTA_QUESTOES_RAIZ)
    



# NOVO SCRIPT ESPECÍFICO PARA VESTIBULARES DEVE LEVAR EM CONTA QUE A SEPARAÇÃO DEVE SER FEITA POR [IMAGEM_n]