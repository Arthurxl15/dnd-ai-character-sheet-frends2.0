import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader, PdfWriter
import json
import math

# --- CONFIGURAÇÃO DA IA ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- BANCO DE DADOS DE REGRAS ---
CLASSES_DND = {
    "Guerreiro": {"dado": 10, "pdf": "DnD 5e - Ficha - Guerreiro - Editável.pdf", "subs": ["Campeão", "Mestre de Batalha", "Cavaleiro Arcano"]},
    "Mago": {"dado": 6, "pdf": "DnD 5e - Ficha - Mago - Editável.pdf", "subs": ["Evocação", "Abjuração", "Ilusão", "Necromancia"]},
    "Ladino": {"dado": 8, "pdf": "DnD 5e - Ficha - Ladino - Editável.pdf", "subs": ["Assassino", "Gatuno", "Trapaceiro Arcano"]},
    "Bárbaro": {"dado": 12, "pdf": "DnD 5e - Ficha - Bárbaro - Editável.pdf", "subs": ["Caminho do Berserker", "Caminho do Totem"]},
    "Bardo": {"dado": 8, "pdf": "DnD 5e - Ficha - Bardo - Editável.pdf", "subs": ["Colégio do Saber", "Colégio da Bravura"]},
    "Clérigo": {"dado": 8, "pdf": "DnD 5e - Ficha - Clérigo - Editável.pdf", "subs": ["Domínio da Vida", "Domínio da Guerra", "Domínio da Luz"]},
    "Paladino": {"dado": 10, "pdf": "DnD 5e - Ficha - Paladino - Editável.pdf", "subs": ["Juramento de Devoção", "Juramento de Vingança"]},
    "Patrulheiro": {"dado": 10, "pdf": "DnD 5e - Ficha - Patrulheiro - Editável.pdf", "subs": ["Caçador", "Mestre das Bestas"]}
}

RACAS = ["Anão", "Elfo", "Humano", "Halfling", "Draconato", "Tiefling", "Gnomo", "Meio-Elfo", "Meio-Orc"]
TENDENCIAS = ["Leal e Bom", "Neutro e Bom", "Caótico e Bom", "Leal e Neutro", "Neutro", "Caótico e Neutro", "Leal e Mau", "Neutro e Mau", "Caótico e Mau"]
ANTECEDENTES = ["Acólito", "Charlatão", "Criminoso", "Entretenimento", "Herói do Povo", "Artesão de Guilda", "Eremita", "Nobre", "Forasteiro", "Sábio", "Marinheiro", "Soldado", "Órfão"]

# --- FUNÇÕES ---
def calc_mod(v): return math.floor((v - 10) / 2)
def calc_prof(n): return math.ceil(1 + (n / 4))

# --- INTERFACE ---
st.set_page_config(page_title="Gerador D&D 5e", layout="wide")
st.title("🛡️ Gerador de Fichas D&D 5e Oficial")

col1, col2 = st.columns(2)

with col1:
    st.header("1. Personagem")
    
    # Seleção de Nome
    tipo_nome = st.radio("Nome do Personagem:", ["Eu quero escrever", "IA sugere um nome"])
    nome_final = st.text_input("Escreva o nome:") if tipo_nome == "Eu quero escrever" else ""
    
    raca_sel = st.selectbox("Raça", RACAS)
    classe_sel = st.selectbox("Classe", list(CLASSES_DND.keys()))
    subclasse_sel = st.selectbox("Subclasse (Arquétipo)", CLASSES_DND[classe_sel]["subs"])
    
    nivel_sel = st.slider("Nível", 1, 20, 1)
    tendencia_sel = st.selectbox("Tendência", TENDENCIAS)
    antecedente_sel = st.selectbox("Antecedente", ANTECEDENTES)

with col2:
    st.header("2. Atributos (8-15)")
    c1, c2 = st.columns(2)
    f_b = c1.number_input("Força", 8, 15, 10)
    d_b = c2.number_input("Destreza", 8, 15, 10)
    c_b = c1.number_input("Constituição", 8, 15, 10)
    i_b = c2.number_input("Inteligência", 8, 15, 10)
    s_b = c1.number_input("Sabedoria", 8, 15, 10)
    ca_b = c2.number_input("Carisma", 8, 15, 10)

if st.button("✨ Gerar Personagem e Criar PDF"):
    with st.spinner("A IA está organizando sua ficha..."):
        
        # IA gera o nome se necessário e detalhes extras
        prompt = f"Crie um personagem D&D 5e: {raca_sel} {classe_sel} ({subclasse_sel}). Tendência: {tendencia_sel}. Antecedente: {antecedente_sel}. {f'Nome: {nome_final}' if nome_final else 'Sugira um nome épico.'} Retorne APENAS um JSON com: 'nome_escolhido', 'historia_curta', 'equipamento'."
        
        response = model.generate_content(prompt)
        extra = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
        
        # Cálculos Matemáticos
        prof = calc_prof(nivel_sel)
        mod_con = calc_mod(c_b)
        hp_max = CLASSES_DND[classe_sel]["dado"] + mod_con + ((nivel_sel-1) * (CLASSES_DND[classe_sel]["dado"] // 2 + 1 + mod_con))

        # Mapeamento para o PDF
        campos_pdf = {
            "Front_Character Name": extra["nome_escolhido"],
            "Front_Race": raca_sel,
            "Front_Level": str(nivel_sel),
            "Front_Alignment": tendencia_sel,
            "Front_Background": antecedente_sel,
            "Front_Archetype": subclasse_sel,
            "Front_Proficiency": f"+{prof}",
            "Front_Str Score": str(f_b), "Front_Str Mod": f"{calc_mod(f_b):+}",
            "Front_Dex Score": str(d_b), "Front_Dex Mod": f"{calc_mod(d_b):+}",
            "Front_Con Score": str(c_b), "Front_Con Mod": f"{calc_mod(c_b):+}",
            "Front_Int Score": str(i_b), "Front_Int Mod": f"{calc_mod(i_b):+}",
            "Front_Wis Score": str(s_b), "Front_Wis Mod": f"{calc_mod(s_b):+}",
            "Front_Cha Score": str(ca_b), "Front_Cha Mod": f"{calc_mod(ca_b):+}",
            "Front_Max HP": str(hp_max),
            "Front_AC": str(10 + calc_mod(d_b)),
            "Front_Initiative": f"{calc_mod(d_b):+}"
        }

        try:
            # Carregar o modelo de PDF da pasta 'modelos'
            reader = PdfReader(f"modelos/{CLASSES_DND[classe_sel]['pdf']}")
            writer = PdfWriter()
            writer.add_page(reader.pages[0])
            writer.update_page_form_field_values(writer.pages[0], campos_pdf)
            
            output_file = f"Ficha_{extra['nome_escolhido']}.pdf"
            with open(output_file, "wb") as f:
                writer.write(f)
            
            st.success(f"Ficha de {extra['nome_escolhido']} gerada com sucesso!")
            with open(output_file, "rb") as f:
                st.download_button("📥 Baixar Ficha PDF", f, file_name=output_file)
                
        except Exception as e:
            st.error(f"Erro ao acessar o PDF: {e}. Certifique-se de que os arquivos estão na pasta 'modelos'.")
