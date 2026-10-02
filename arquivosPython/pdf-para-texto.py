import fitz  # PyMuPDF
import os

def processar_pdf(caminho_pdf, pasta_destino="resultado_extracao"):
    # Pega o diretório onde o script está sendo executado para salvar o TXT na raiz
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # 1. Configuração de pastas (Apenas para imagens agora)
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
    
    pasta_imagens = os.path.join(pasta_destino, "imagens")
    if not os.path.exists(pasta_imagens):
        os.makedirs(pasta_imagens)

    # 2. Abrir o documento
    doc = fitz.open(caminho_pdf)
    texto_acumulado = ""
    img_count = 0

    print(f"--- Iniciando Processamento: {caminho_pdf} ---")
    print(f"Total de páginas: {doc.page_count}")

    for i in range(len(doc)):
        pagina = doc[i]
        num_pag = i + 1
        
        # --- PARTE A: Extração de Texto ---
        blocos = pagina.get_text("blocks")
        blocos.sort(key=lambda b: (b[1], b[0]))
        
        texto_acumulado += f"\n--- PÁGINA {num_pag} ---\n"
        for b in blocos:
            texto_acumulado += b[4] + "\n"

        # --- PARTE B: Extração de Imagens ---
        lista_imagens = pagina.get_images(full=True)
        
        for img_index, img in enumerate(lista_imagens):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]
            
            nome_img = f"pag_{num_pag}_img_{img_index}.{ext}"
            caminho_img = os.path.join(pasta_imagens, nome_img)
            
            with open(caminho_img, "wb") as f:
                f.write(image_bytes)
            img_count += 1

    # 3. Salvar o arquivo de texto na RAIZ (Base)
    # Usamos o BASE_DIR para garantir que saia da pasta 'resultado_extracao'
    caminho_txt = os.path.join(BASE_DIR, "texto_extraido.txt")
    
    with open(caminho_txt, "w", encoding="utf-8") as f:
        f.write(texto_acumulado)

    print(f"\n--- Processo Finalizado com Sucesso ---")
    print(f"Txt gerado na BASE: {caminho_txt}")
    print(f"Imagens salvas em: {pasta_imagens} (Total: {img_count})")

if __name__ == "__main__":
    arquivo = "arquivo.pdf" 
    if os.path.exists(arquivo):
        processar_pdf(arquivo)
    else:
        print(f"Erro: Arquivo {arquivo} não encontrado.")