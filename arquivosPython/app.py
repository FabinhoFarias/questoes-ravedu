import os
import json
import re
import streamlit as st

# --- CONFIGURAÇÃO DE CAMINHOS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PASTA_QUESTOES_RAIZ = os.path.join(BASE_DIR, 'Questoes')

def extrair_numero_lote(nome_pasta):
    """Auxiliar para ordenar as pastas pelo número do lote de forma correta"""
    numeros = re.findall(r'\d+', nome_pasta)
    return int(numeros[0]) if numeros else 0

def carregar_lotes_disponiveis(caminho_especifico):
    """Varre o diretório específico em busca de estruturas loteEnem ou loteVest"""
    if not os.path.exists(caminho_especifico):
        return []
    pastas = [
        p for p in os.listdir(caminho_especifico) 
        if (p.startswith("loteEnem") or p.startswith("loteVest")) 
        and os.path.isdir(os.path.join(caminho_especifico, p))
    ]
    return sorted(pastas, key=extrair_numero_lote)

def renderizar_texto_com_imagens(texto, lista_arquivos, pasta_imagens):
    """Injeta as tags [IMAGEM_n] dinamicamente como componentes st.image no Streamlit"""
    regex = r'(\[IMAGEM_\d+\])'
    partes = re.split(regex, texto)
    
    for parte in partes:
        match = re.match(r'\[IMAGEM_(\d+)\]', parte)
        if match:
            idx_img = int(match.group(1))
            if idx_img < len(lista_arquivos):
                nome_arquivo = lista_arquivos[idx_img]
                caminho_completo_img = os.path.join(pasta_imagens, nome_arquivo)
                if os.path.exists(caminho_completo_img):
                    st.image(caminho_completo_img, caption=f"Imagem Contexto [{idx_img}]", use_container_width=False)
                else:
                    st.warning(f"⚠️ Mídia local não encontrada: {nome_arquivo}")
            else:
                st.error(f"❌ Tag {parte} aponta para um índice inexistente na lista de arquivos.")
        else:
            if parte.strip():
                st.write(parte)

def main():
    st.set_page_config(page_title="Editor de Lotes ENEM", layout="wide")
    st.title("🛠️ Painel Curador - Edição de Lotes de Questões")

    # --- BARRA LATERAL: NAVEGAÇÃO MULTI-ÁREAS E DISCIPLINAS ---
    st.sidebar.header("📁 Seleção de Área e Lote")
    
    area_selecionada = st.sidebar.selectbox("Escolha a Grande Área:", ["MATEMATICA", "NATUREZA", "HUMANAS", "LINGUAGENS"])
    
    caminho_busca_lotes = os.path.join(PASTA_QUESTOES_RAIZ, area_selecionada)
    sub_materia = ""
    
    if area_selecionada == "NATUREZA":
        sub_materia = st.sidebar.selectbox("Escolha a Disciplina:", ["biologia", "fisica", "quimica"])
    elif area_selecionada == "HUMANAS":
        sub_materia = st.sidebar.selectbox("Escolha a Disciplina:", ["filosofia", "sociologia", "historia", "geografia"])
    elif area_selecionada == "LINGUAGENS":
        sub_materia = st.sidebar.selectbox("Escolha a Disciplina:", ["gramatica", "interpretacaodetexto", "literatura"])

    caminho_busca_lotes = os.path.join(caminho_busca_lotes, sub_materia)

    lotes = carregar_lotes_disponiveis(caminho_busca_lotes)
    
    if not lotes:
        st.sidebar.error(f"Nenhuma pasta 'loteEnem' ou 'loteVest' foi localizada no diretório: /Questoes/{area_selecionada}/{sub_materia}")
        return

    pasta_lote_selecionada = st.sidebar.selectbox("Escolha o Lote:", lotes)
    
    caminho_pasta_lote = os.path.join(caminho_busca_lotes, pasta_lote_selecionada)
    caminho_imagens_lote = os.path.join(caminho_pasta_lote, 'imagensQuestoes')
    caminho_json_lote = os.path.join(caminho_pasta_lote, f"questoes_{pasta_lote_selecionada}.json")

    if not os.path.exists(caminho_json_lote):
        st.sidebar.error(f"Arquivo questoes_{pasta_lote_selecionada}.json não existe.")
        return

    with open(caminho_json_lote, 'r', encoding='utf-8') as f:
        dados_lote = json.load(f)

    if not dados_lote:
        st.sidebar.warning("Este lote está vazio.")
        return

    # --- NAVEGAÇÃO ENTRE QUESTÕES (SETAS) ---
    total_questoes = len(dados_lote)
    st.sidebar.markdown(f"🔢 *Este lote possui {total_questoes} questões.*")
    
    ch_index = f"idx_questao_{area_selecionada}_{sub_materia}_{pasta_lote_selecionada}"
    if ch_index not in st.session_state:
        st.session_state[ch_index] = 0

    st.sidebar.write("Navegar pelas questões:")
    col_ant, col_num, col_prox = st.sidebar.columns([1, 2, 1])
    
    if col_ant.button("◀", disabled=st.session_state[ch_index] == 0):
        st.session_state[ch_index] -= 1
        st.rerun()
        
    col_num.markdown(f"<center><b>{st.session_state[ch_index] + 1} / {total_questoes}</b></center>", unsafe_allow_html=True)
    
    if col_prox.button("▶", disabled=st.session_state[ch_index] >= total_questoes - 1):
        st.session_state[ch_index] += 1
        st.rerun()
        
    idx_questao = st.session_state[ch_index]
    numero_questao_selecionada = idx_questao + 1
    questao = dados_lote[idx_questao]

    # --- ALINHAMENTO PREVENTIVO DE ERROS (ANTI-CRASH) ---
    max_comp = 8 if area_selecionada == "NATUREZA" else (9 if area_selecionada == "LINGUAGENS" else 7)
    comp_original = questao.get("competencia", 1)
    
    try:
        comp_validada = int(comp_original)
    except (ValueError, TypeError):
        comp_validada = 1

    erro_detectado = False
    motivos_erro = []

    if comp_validada > max_comp:
        motivos_erro.append(f"Competência no JSON ({comp_original}) ultrapassa o limite permitido para {area_selecionada} (máx: {max_comp}).")
        comp_validada = 1
        erro_detectado = True

    hab_original = str(questao.get("habilidade", "H1"))
    num_hab_match = re.search(r'\d+', hab_original)
    if num_hab_match:
        if int(num_hab_match.group()) > 30:
            motivos_erro.append(f"Habilidade no JSON ({hab_original}) ultrapassa o limite padrão de 30 (máx: H30).")
            hab_original = "H1"
            erro_detectado = True
    else:
        motivos_erro.append(f"Habilidade sem formato numérico reconhecível: '{hab_original}'.")
        hab_original = "H1"
        erro_detectado = True

    if erro_detectado:
        st.error("🚨 **Inconsistência de Limites Detectada!** Valores resetados temporariamente para exibição segura.")
        st.warning(f"📍 **Endereço do Erro:** `Questoes/{area_selecionada}/{sub_materia}/{pasta_lote_selecionada}/questoes_{pasta_lote_selecionada}.json` ➡️ **Questão nº {numero_questao_selecionada}**")
        for motivo in motivos_erro:
            st.info(f"🔎 **Diagnóstico:** {motivo}")

    # --- CORPO PRINCIPAL: VISUALIZAÇÃO E FORMULÁRIO ---
    st.subheader(f"Análise da Questão {numero_questao_selecionada} de {total_questoes}: {questao.get('title')}")
    
    with st.container(border=True):
        renderizar_texto_com_imagens(questao.get("contexto", ""), questao.get("arquivos", []), caminho_imagens_lote)
        st.markdown(f"**{questao.get('introducao_alternativas', '')}**")
        
        st.markdown("---")
        for alt in questao.get("alternativas", []):
            col_letra, col_conteudo = st.columns([1, 15])
            col_letra.markdown(f"### `{alt['letra']}`")
            if alt.get("texto"):
                col_conteudo.write(alt["texto"])
            if alt.get("imagem_url"):
                caminho_img_alt = os.path.join(caminho_imagens_lote, alt["imagem_url"])
                if os.path.exists(caminho_img_alt):
                    col_conteudo.image(caminho_img_alt, width=250)
            if alt.get("e_correta"):
                col_conteudo.caption("🟢 *Alternativa marcada como CORRETA no banco.*")

    st.markdown("---")
    st.subheader("📝 Editor de Metadados e Textos Físicos")

    # 🔑 CHAVE ÚNICA DO FORMULÁRIO VINCULADA AO ÍNDICE DA QUESTÃO ATUAL
    with st.form(key=f"form_edicao_questao_{idx_questao}"):
        col1, col2, col3 = st.columns(3)
        novo_titulo = col1.text_input("Título da Questão:", value=questao.get("title", ""), key=f"title_{idx_questao}")
        novo_assunto = col2.text_input("Assunto:", value=questao.get("assunto", ""), key=f"assunto_{idx_questao}")
        
        dificuldade_salva = questao.get("dificuldade", "Médio")
        if dificuldade_salva == "Medio": dificuldade_salva = "Médio"
        elif dificuldade_salva == "Facil": dificuldade_salva = "Fácil"
        elif dificuldade_salva == "Dificil": dificuldade_salva = "Difícil"

        nova_dif = col3.selectbox(
            "Dificuldade:", 
            ["Fácil", "Médio", "Difícil"], 
            index=["Fácil", "Médio", "Difícil"].index(dificuldade_salva),
            key=f"dif_{idx_questao}"
        )
        col4, col5 = st.columns(2)
        nova_comp = col4.number_input("Competência (ENEM):", min_value=1, max_value=max_comp, value=comp_validada, key=f"comp_{idx_questao}")
        nova_hab = col5.text_input("Habilidade (Ex: H7 ou 7):", value=hab_original, key=f"hab_{idx_questao}")

        novo_contexto = st.text_area("Texto do Contexto (mantenha as tags [IMAGEM_n]):", value=questao.get("contexto", ""), height=150, key=f"contexto_{idx_questao}")
        nova_intro = st.text_area("Introdução das Alternativas:", value=questao.get("introducao_alternativas", ""), height=80, key=f"intro_{idx_questao}")

        st.markdown("#### Editar Textos das Alternativas")
        novas_alternativas = []
        for i, alt in enumerate(questao.get("alternativas", [])):
            col_a, col_b, col_c = st.columns([2, 10, 4])
            col_a.write(f"Alternativa **{alt['letra']}**")
            
            # 💡 INCLUSÃO DO `idx_questao` NAS CHAVES DOS COMPONENTES FILHOS
            texto_editado = col_b.text_input(
                f"Texto da Alternativa {alt['letra']}:", 
                value=alt.get("texto", ""), 
                key=f"txt_q{idx_questao}_{alt['letra']}_{i}"
            )
            correta_editada = col_c.checkbox(
                "É a correta", 
                value=alt.get("e_correta", False), 
                key=f"chk_q{idx_questao}_{alt['letra']}_{i}"
            )
            
            novas_alternativas.append({
                "letra": alt["letra"],
                "texto": texto_editado,
                "e_correta": correta_editada,
                "imagem_url": alt.get("imagem_url")
            })

        botao_salvar = st.form_submit_button("💾 Gravar Alterações no Arquivo JSON", use_container_width=True)
        
        if botao_salvar:
            hab_salvamento = nova_hab.strip()
            if hab_salvamento.isdigit():
                hab_salvamento = f"H{hab_salvamento}"

            questao["title"] = novo_titulo
            questao["assunto"] = novo_assunto
            questao["dificuldade"] = nova_dif
            questao["competencia"] = int(nova_comp)
            questao["habilidade"] = hab_salvamento
            questao["contexto"] = novo_contexto.replace("\\n", "\n").replace("/n", "\n")
            questao["introducao_alternativas"] = nova_intro
            questao["alternativas"] = novas_alternativas

            dados_lote[idx_questao] = questao

            try:
                with open(caminho_json_lote, 'w', encoding='utf-8') as f:
                    json.dump(dados_lote, f, indent=2, ensure_ascii=False)
                st.success(f"🎉 Alterações aplicadas com sucesso no arquivo físico: `questoes_{pasta_lote_selecionada}.json`!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Falha crítica de I/O ao gravar arquivo: {e}")

if __name__ == "__main__":
    main()