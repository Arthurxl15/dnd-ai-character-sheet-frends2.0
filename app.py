import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader, PdfWriter
import json
import math

# --- CONFIGURAÇÃO DA IA ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- DADOS DE REGRAS ---
CLASSES_DND = {
    "Guerreiro": {"dado": 10, "pdf": "DnD 5e - Ficha - Guerreiro - Editável.pdf", "subs": ["Campeão", "Mestre de Batalha", "Cavaleiro Arcano", "Samurai", "Cavaleiro Rúnico"]},
    "Mago": {"dado": 6, "pdf": "DnD 5e - Ficha - Mago - Editável.pdf", "subs": ["Evocação", "Abjuração", "Adivinhação", "Lâmina Cantante"]},
    "Ladino": {"dado": 8, "pdf": "DnD 5e - Ficha - Ladino - Editável.pdf", "subs": ["Assassino", "Gatuno", "Trapaceiro Arcano", "Faca Psíquica"]},
    "Paladino": {"dado": 10, "pdf": "DnD 5e - Ficha - Paladino - Editável.pdf", "subs": ["Devoção", "Vingança", "Anciões"]},
    "Patrulheiro": {"dado": 10, "pdf": "DnD 5e - Ficha - Patrulheiro - Editável.pdf", "subs": ["Caçador", "Mestre das Bestas", "Perseguidor Sombrio"]}
}

MATRIZ_PADRAO = [15, 14, 13, 12, 10, 8]
RACAS = ["Anão", "Elfo", "Humano", "Halfling", "Draconato", "Shadar-kai", "Tiefling"]

# --- FUNÇÕES ---
def calc_mod(v): return math.floor((v - 10) / 2)
def calc_prof(n): return math.ceil(1 + (n / 4))

st.set_page_config(page_title="D&D Beyond Clone", layout="wide")
st.title("🛡️ Criador de Fichas: Regra de Matriz Padrão")

col1, col2 = st.columns(2)

with col1:
    st.header("1. Identidade")
    tipo_nome = st.radio("Nome do Personagem:", ["Eu escrevo", "IA gera"])
    nome_input = st.text_input("Nome:") if tipo_nome == "Eu escrevo" else ""
    
    raca_sel = st.selectbox("Raça", RACAS)
    classe_sel = st.selectbox("Classe", list(CLASSES_DND.keys()))
    subclasse_sel = st.selectbox("Subclasse", CLASSES_DND[classe_sel]["subs"])
    nivel_sel = st.slider("Nível", 1, 20, 1)

with col2:
    st.header("2. Atributos (Matriz Padrão)")
    st.info("Escolha um valor diferente para cada atributo: 15, 14, 13, 12, 10, 8")
    
    c1, c2 = st.columns(2)
    f_b = c1.selectbox("Força", MATRIZ_PADRAO, index=0)
    d_b = c2.selectbox("Destreza", MATRIZ_PADRAO, index=1)
    c_b = c1.selectbox("Constituição", MATRIZ_PADRAO, index=2)
    i_b = c2.selectbox("Inteligência", MATRIZ_PADRAO, index=3)
    s_b = c1.selectbox("Sabedoria", MATRIZ_PADRAO, index=4)
    ca_b = c2.selectbox("Carisma", MATRIZ_PADRAO, index=5)

    # Validação de Duplicados
    escolhas = [f_b, d_b, c_b, i_b, s_b, ca_b]
    if len(set(escolhas)) != 6:
        st.error("⚠️ Erro: Não podes repetir números! Cada valor da matriz deve ser usado apenas uma vez.")
        pode_gerar = False
    else:
        st.success("✅ Atributos válidos!")
        pode_gerar = True

# --- GERAÇÃO DO PDF ---
if st.button("🔥 Gerar e Baixar Ficha") and pode_gerar:
    with st.spinner("IA a consultar o Livro do Jogador..."):
        
        prompt = f"Gere dados D&D 5e: {raca_sel} {classe_sel} nível {nivel_sel}. {f'Nome: {nome_input}' if nome_input else 'Gere um nome oficial.'} Retorne JSON: {{'nome': '...', 'tendencia': '...', 'antecedente': '...'}}"
        
        response = model.generate_content(prompt)
        extra = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
        
        prof = calc_prof(nivel_sel)
        mod_con = calc_mod(c_b)
        hp = CLASSES_DND[classe_sel]["dado"] + mod_con + ((nivel_sel-1)*(CLASSES_DND[classe_sel]["dado"]//2 + 1 + mod_con))

        dados_pdf = {
            "Front_Character Name": extra["nome"],
            "Front_Race": raca_sel,
            "Front_Level": str(nivel_sel),
            "Front_Archetype": subclasse_sel,
            "Front_Proficiency": f"+{prof}",
            "Front_Str Score": str(f_b), "Front_Str Mod": f"{calc_mod(f_b):+}",
            "Front_Dex Score": str(d_b), "Front_Dex Mod": f"{calc_mod(d_b):+}",
            "Front_Con Score": str(c_b), "Front_Con Mod": f"{calc_mod(c_b):+}",
            "Front_Int Score": str(i_b), "Front_Int Mod": f"{calc_mod(i_b):+}",
            "Front_Wis Score": str(s_b), "Front_Wis Mod": f"{calc_mod(s_b):+}",
            "Front_Cha Score": str(ca_b), "Front_Cha Mod": f"{calc_mod(ca_b):+}",
            "Front_Max HP": str(hp),
            "Front_AC": str(10 + calc_mod(d_b)),
            "Front_Initiative": f"{calc_mod(d_b):+}"
        }

        try:
            reader = PdfReader(f"modelos/{CLASSES_DND[classe_sel]['pdf']}")
            writer = PdfWriter()
            writer.add_page(reader.pages[0])
            writer.update_page_form_field_values(writer.pages[0], dados_pdf)
            
            output = f"Ficha_{extra['nome']}.pdf"
            with open(output, "wb") as f:
                writer.write(f)
            
            st.success(f"Ficha de {extra['nome']} gerada!")
            with open(output, "rb") as f:
                st.download_button("📥 Baixar PDF", f, file_name=output)
        except Exception as e:
            st.error(f"Erro ao abrir PDF. Verifique a pasta 'modelos'.")
