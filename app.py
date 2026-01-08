import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader, PdfWriter
import json

# Conexão com a Chave configurada no painel Secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3-flash-preview')

def preencher_pdf(classe, dados_ia, arquivos_pdf):
    # Procura o arquivo PDF correspondente na sua lista de uploads
    nome_arquivo = f"DnD 5e - Ficha - {classe} - Editável.pdf"
    reader = PdfReader(nome_arquivo)
    writer = PdfWriter()
    writer.add_page(reader.pages[0])

    # Mapeamento: 'Nome no PDF' : 'Dado da IA'
    mapeamento = {
        "NOME DE PERSONAGEM": dados_ia.get("nome"),
        "RAÇA": dados_ia.get("raca"),
        "FORÇA": str(dados_ia.get("for")),
        "DESTREZA": str(dados_ia.get("des")),
        "CONSTITUIÇÃO": str(dados_ia.get("con")),
        "INTELIGÊNCIA": str(dados_ia.get("int")),
        "SABEDORIA": str(dados_ia.get("sab")),
        "CARISMA": str(dados_ia.get("car"))
    }

    writer.update_page_form_field_values(writer.pages[0], mapeamento)
    
    saida = "ficha_finalizada.pdf"
    with open(saida, "wb") as f:
        writer.write(f)
    return saida

# Interface
st.title("🎲 D&D 5e Auto-Ficha (LDJ, Tasha, Xanathar)")
classe = st.selectbox("Escolha sua Classe", ["Guerreiro", "Monge", "Mago", "Ladino", "Bardo", "Bruxo", "Clérigo", "Druida", "Bárbaro", "Feiticeiro"])
nivel = st.slider("Nível do Personagem", 1, 20, 1)

if st.button("✨ Gerar Personagem com Gemini 3 Flash"):
    prompt = f"Gere uma ficha de D&D 5e para um {classe} nível {nivel}. Responda APENAS em JSON com: nome, raca, for, des, con, int, sab, car."
    
    response = model.generate_content(prompt)
    dados = json.loads(response.text.replace('```json', '').replace('```', ''))
    
    arquivo_pdf = preencher_pdf(classe, dados, None)
    
    with open(arquivo_pdf, "rb") as f:
        st.download_button(f"📥 Baixar Ficha de {classe} (PDF)", f, file_name=f"Ficha_{classe}.pdf")
