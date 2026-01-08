import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader, PdfWriter
import json

# Configuração da API (Pegue o valor nos Secrets do Streamlit)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3-flash-preview')

def gerar_ficha_ia(classe, nivel):
    prompt = f"""
    Gere uma ficha de D&D 5e para um {classe} nível {nivel}. 
    Use livros: PHB, Tasha e Xanathar.
    Retorne APENAS um JSON puro com as chaves: 
    "nome", "raca", "for", "des", "con", "int", "sab", "car", "habilidades".
    """
    response = model.generate_content(prompt)
    # Limpa a resposta para garantir que seja um JSON válido
    dados = json.loads(response.text.replace('```json', '').replace('```', ''))
    return dados

def preencher_pdf(classe, dados_ia):
    # Seleciona o arquivo certo com base na classe
    caminho_modelo = f"modelos/DnD 5e - Ficha - {classe} - Editável.pdf"
    reader = PdfReader(caminho_modelo)
    writer = PdfWriter()
    
    page = reader.pages[0]
    writer.add_page(page)

    # Mapeamento dos campos do seu PDF
    # Nota: Você precisará conferir os nomes exatos dos campos no PDF
    campos = {
        "NOME DO PERSONAGEM": dados_ia["nome"],
        "RAÇA": dados_ia["raca"],
        "FORÇA": str(dados_ia["for"]),
        "DESTREZA": str(dados_ia["des"]),
        "CONSTITUIÇÃO": str(dados_ia["con"]),
        "INTELIGÊNCIA": str(dados_ia["int"]),
        "SABEDORIA": str(dados_ia["sab"]),
        "CARISMA": str(dados_ia["car"]),
    }

    writer.update_page_form_field_values(writer.pages[0], campos)
    
    caminho_saida = "ficha_preenchida.pdf"
    with open(caminho_saida, "wb") as f:
        writer.write(f)
    return caminho_saida

# Interface
st.title("🎲 Gerador Automático de Fichas (LDJ + Tasha + Xanathar)")
classe = st.selectbox("Classe", ["Guerreiro", "Mago", "Ladino", "Monge", "Bardo", "Bruxo", "Clérigo", "Druida", "Bárbaro", "Feiticeiro"])
nivel = st.slider("Nível", 1, 20, 1)

if st.button("Gerar e Preencher PDF"):
    with st.spinner("A IA está montando seu personagem..."):
        dados = gerar_ficha_ia(classe, nivel)
        arquivo = preencher_pdf(classe, dados)
        
        with open(arquivo, "rb") as f:
            st.download_button("📥 Baixar Ficha PDF Pronta", f, file_name=f"Ficha_{classe}.pdf")
