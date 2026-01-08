import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader, PdfWriter
import json
import math

# --- 1. CONFIGURAÇÃO DA IA ---
# Certifique-se de que a chave está no Secrets do Streamlit como GEMINI_API_KEY
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # CORREÇÃO: Usando o nome oficial do modelo estável
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Erro ao configurar chave de API: {e}")

# --- 2. BANCO DE DADOS (PHB + Xanathar + Tasha + Mordenkainen) ---
RACAS_COMPLETAS = [
    "Anão (Colina)", "Anão (Montanha)", "Anão (Duergar)",
    "Elfo (Alto)", "Elfo (Floresta)", "Elfo (Drow)", "Elfo (Shadar-kai)", "Elfo (Eladrin)",
    "Halfling (Pés Leves)", "Halfling (Robusto)", "Humano (Padrão)", "Humano (Variante)",
    "Draconato", "Gnomo (Floresta)", "Gnomo (Rocha)", "Meio-Elfo", "Meio-Orc", "Tiefling",
    "Aasimar", "Tabaxi", "Goliath", "Firbolg", "Kenku", "Tortle", "Harengon", "Changeling",
    "Genasi (Ar/Terra/Fogo/Água)", "Tritão", "Lizardfolk"
]

CLASSES_DND = {
    "Bárbaro": {"dado": 12, "pdf": "DnD 5e - Ficha - Bárbaro - Editável.pdf", 
                "subs": ["Berserker", "Totêmico", "Zelote", "Guardião Ancestral", "Besta", "Magia Selvagem"]},
    "Bardo": {"dado": 8, "pdf": "DnD 5e - Ficha - Bardo - Editável.pdf", 
              "subs": ["Saber", "Valor", "Espadas", "Sussurros", "Eloquência", "Criação"]},
    "Bruxo": {"dado": 8, "pdf": "DnD 5e - Ficha - Bruxo - Editável.pdf", 
              "subs": ["Arquifada", "Infernal", "Hexblade", "O Gênio", "O Profundo"]},
    "Clérigo": {"dado": 8, "pdf": "DnD 5e - Ficha - Clérigo - Editável.pdf", 
                "subs": ["Vida", "Guerra", "Forja", "Sepultura", "Ordem", "Crepúsculo", "Paz"]},
    "Druida": {"dado": 8, "pdf": "DnD 5e - Ficha - Druída - Editável.pdf", 
               "subs": ["Terra", "Lua", "Sonhos", "Pastor", "Esporos", "Estrelas", "Fogo Selvagem"]},
    "Feiticeiro": {"dado": 6, "pdf": "DnD 5e - Ficha - Feiticeiro - Editável.pdf", 
                   "subs": ["Dracônica", "Magia Selvagem", "Sombra", "Alma Divina", "Mente Aberrante"]},
    "Guerreiro": {"dado": 10, "pdf": "DnD 5e - Ficha - Guerreiro - Editável.pdf", 
                  "subs": ["Campeão", "Mestre de Batalha", "Cavaleiro Arcano", "Samurai", "Cavaleiro Rúnico"]},
    "Ladino": {"dado": 8, "pdf": "DnD 5e - Ficha - Ladino - Editável.pdf", 
               "subs": ["Assassino", "Gatuno", "Trapaceiro Arcano", "Espadachim", "Fantasma", "Lâmina Psíquica"]},
    "Mago": {"dado": 6, "pdf": "DnD 5e - Ficha - Mago - Editável.pdf", 
             "subs": ["Abjuração", "Evocação", "Adivinhação", "Magia de Guerra", "Escribas", "Lâmina Cantante"]},
    "Monge": {"dado": 8, "pdf": "DnD 5e - Ficha - Monge - Editável.pdf", 
              "subs": ["Mão Aberta", "Sombras", "Kensei", "Misericórdia", "Eu Astral"]},
    "Paladino": {"dado": 10, "pdf": "DnD 5e - Ficha - Paladino - Editável.pdf", 
                 "subs": ["Devoção", "Vingança", "Conquista", "Redenção", "Glória", "Vigilância"]},
    "Patrulheiro": {"dado": 10, "pdf": "DnD 5e - Ficha - Patrulheiro - Editável.pdf", 
                    "subs": ["Caçador", "Mestre das Bestas", "Perseguidor Sombrio", "Guardião de Dracos"]}
}

TENDENCIAS = ["Leal e Bom", "Neutro e Bom", "Caótico e Bom", "Leal e Neutro", "Neutro", "Caótico e Neutro", "Leal e Mau", "Neutro e Mau", "Caótico e Mau"]
ANTECEDENTES = ["Acólito", "Charlatão", "Criminoso", "Entretenimento", "Herói do Povo", "Artesão de Guilda", "Eremita", "Nobre", "Forasteiro", "Sábio", "Marinheiro", "Soldado", "Órfão"]
MATRIZ_PADRAO = [15, 14, 13, 12, 10, 8]

# --- 3. FUNÇÕES ---
def calc_mod(v): return math.floor((v - 10) / 2)
def calc_prof(n): return math.ceil(1 + (n / 4))

# --- 4. INTERFACE ---
st.set_page_config(page_title="D&D 5e Ultimate Generator", layout="wide")
st.title("🛡️ Criador de Fichas D&D 5e (PHB + Xanathar + Tasha)")

col1, col2 = st.columns(2)

with col1:
    st.header("1. Personagem")
    tipo_nome = st.radio("Nome:", ["Eu escrevo", "IA sugere"])
    nome_input = st.text_input("Escreva o nome:") if tipo_nome == "Eu escrevo" else ""
    
    raca_sel = st.selectbox("Raça", RACAS_COMPLETAS)
    classe_sel = st.selectbox("Classe", list(CLASSES_DND.keys()))
    sub_sel = st.selectbox("Subclasse", CLASSES_DND[classe_sel]["subs"])
    nivel_sel = st.slider("Nível", 1, 20, 1)
    tend_sel = st.selectbox("Tendência", TENDENCIAS)
    ant_sel = st.selectbox("Antecedente", ANTECEDENTES)

with col2:
    st.header("2. Atributos (Matriz Padrão)")
    st.info("Escolha cada valor uma única vez: 15, 14, 13, 12, 10, 8")
    c_a, c_b = st.columns(2)
    f_b = c_a.selectbox("Força", MATRIZ_PADRAO, index=0)
    d_b = c_b.selectbox("Destreza", MATRIZ_PADRAO, index=1)
    c_b_val = c_a.selectbox("Constituição", MATRIZ_PADRAO, index=2)
    i_b = c_b.selectbox("Inteligência", MATRIZ_PADRAO, index=3)
    s_b = c_a.selectbox("Sabedoria", MATRIZ_PADRAO, index=4)
    ca_b = c_b.selectbox("Carisma", MATRIZ_PADRAO, index=5)

    validado = len(set([f_b, d_b, c_b_val, i_b, s_b, ca_b])) == 6
    if not validado: st.error("⚠️ Não repita os números nos atributos!")

# --- 5. GERAÇÃO ---
if st.button("🔥 Gerar e Baixar PDF") and validado:
    with st.spinner("IA processando as regras oficiais..."):
        prompt = f"Crie um personagem D&D 5e: {raca_sel} {classe_sel} ({sub_sel}). Tendência: {tend_sel}. Antecedente: {ant_sel}. {f'Nome: {nome_input}' if nome_input else 'Gere um nome oficial.'} Retorne APENAS um JSON: {{'nome': '...', 'historia': '...'}}"
        
        try:
            response = model.generate_content(prompt)
            # Extração segura do JSON
            texto_limpo = response.text.strip().replace('```json', '').replace('```', '')
            extra = json.loads(texto_limpo)
            
            prof = calc_prof(nivel_sel)
            mod_con = calc_mod(c_b_val)
            hp = CLASSES_DND[classe_sel]["dado"] + mod_con + ((nivel_sel-1) * (CLASSES_DND[classe_sel]["dado"] // 2 + 1 + mod_con))

            dados_pdf = {
                "Front_Character Name": extra["nome"], "Front_Race": raca_sel, "Front_Level": str(nivel_sel),
                "Front_Alignment": tend_sel, "Front_Background": ant_sel, "Front_Archetype": sub_sel,
                "Front_Proficiency": f"+{prof}",
                "Front_Str Score": str(f_b), "Front_Str Mod": f"{calc_mod(f_b):+}",
                "Front_Dex Score": str(d_b), "Front_Dex Mod": f"{calc_mod(d_b):+}",
                "Front_Con Score": str(c_b_val), "Front_Con Mod": f"{calc_mod(c_b_val):+}",
                "Front_Int Score": str(i_b), "Front_Int Mod": f"{calc_mod(i_b):+}",
                "Front_Wis Score": str(s_b), "Front_Wis Mod": f"{calc_mod(s_b):+}",
                "Front_Cha Score": str(ca_b), "Front_Cha Mod": f"{calc_mod(ca_b):+}",
                "Front_Max HP": str(hp), "Front_AC": str(10 + calc_mod(d_b)), "Front_Initiative": f"{calc_mod(d_b):+}"
            }

            reader = PdfReader(f"modelos/{CLASSES_DND[classe_sel]['pdf']}")
            writer = PdfWriter()
            writer.add_page(reader.pages[0])
            writer.update_page_form_field_values(writer.pages[0], dados_pdf)
            
            nome_arq = f"Ficha_{extra['nome'].replace(' ', '_')}.pdf"
            with open(nome_arq, "wb") as f: writer.write(f)
            
            st.success(f"✅ {extra['nome']} gerado com sucesso!")
            with open(nome_arq, "rb") as f:
                st.download_button("📥 Baixar Ficha PDF", f, file_name=nome_arq)

        except Exception as e:
            st.error(f"Ocorreu um erro: {e}")
            st.info("Verifique se os PDFs estão na pasta 'modelos' e se a chave API está correta.")
