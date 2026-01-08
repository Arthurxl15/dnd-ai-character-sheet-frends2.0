import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader, PdfWriter
import json
import math

# --- 1. CONFIGURAÇÃO DA IA ---
# Tente usar gemini-1.5-flash. Se der erro, o log dirá se a chave é o problema.
try:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("🔑 Chave GEMINI_API_KEY não encontrada nos Secrets do Streamlit!")
        st.stop()
        
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # Nome oficial para evitar o erro 404
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Erro ao inicializar IA: {e}")
    st.stop()

# --- 2. BANCO DE DADOS (PHB, XGtE, TCoE, MPMM) ---
RACAS_COMPLETAS = [
    "Anão (Colina)", "Anão (Montanha)", "Elfo (Alto)", "Elfo (Floresta)", "Elfo (Shadar-kai)", 
    "Humano", "Halfling", "Draconato", "Gnomo", "Meio-Elfo", "Meio-Orc", "Tiefling", 
    "Tabaxi", "Aasimar", "Goliath", "Harengon", "Tortle", "Tritão"
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
                 "subs": ["Devoção", "Vingança", "Anciões", "Conquista", "Redenção", "Glória", "Vigilância"]},
    "Patrulheiro": {"dado": 10, "pdf": "DnD 5e - Ficha - Patrulheiro - Editável.pdf", 
                    "subs": ["Caçador", "Mestre das Bestas", "Perseguidor Sombrio", "Andarilho do Horizonte"]}
}

TENDENCIAS = ["Leal e Bom", "Neutro", "Caótico e Bom", "Leal e Neutro", "Caótico e Neutro", "Leal e Mau", "Neutro e Mau", "Caótico e Mau"]
ANTECEDENTES = ["Acólito", "Charlatão", "Criminoso", "Entretenimento", "Herói do Povo", "Nobre", "Forasteiro", "Sábio", "Soldado", "Órfão"]
MATRIZ_PADRAO = [15, 14, 13, 12, 10, 8]

# --- 3. FUNÇÕES ---
def calc_mod(v): return math.floor((v - 10) / 2)
def calc_prof(n): return math.ceil(1 + (n / 4))

# --- 4. INTERFACE ---
st.set_page_config(page_title="D&D Auto-Ficha Pro", layout="wide")
st.title("🎲 Gerador de Fichas D&D 5e")

col1, col2 = st.columns(2)

with col1:
    st.header("1. Identidade")
    tipo_nome = st.radio("Nome do Personagem:", ["Eu escrevo", "IA gera nomes oficiais"])
    nome_input = st.text_input("Escreva o nome:") if tipo_nome == "Eu escrevo" else ""
    
    raca_sel = st.selectbox("Raça", RACAS_COMPLETAS)
    classe_sel = st.selectbox("Classe", list(CLASSES_DND.keys()))
    sub_sel = st.selectbox("Subclasse", CLASSES_DND[classe_sel]["subs"])
    nivel_sel = st.slider("Nível", 1, 20, 1)
    tend_sel = st.selectbox("Tendência", TENDENCIAS)
    ant_sel = st.selectbox("Antecedente", ANTECEDENTES)

with col2:
    st.header("2. Atributos (Matriz Padrão)")
    st.info("Escolha cada valor uma única vez (15, 14, 13, 12, 10, 8)")
    ca1, ca2 = st.columns(2)
    f_b = ca1.selectbox("Força", MATRIZ_PADRAO, index=0)
    d_b = ca2.selectbox("Destreza", MATRIZ_PADRAO, index=1)
    c_b = ca1.selectbox("Constituição", MATRIZ_PADRAO, index=2)
    i_b = ca2.selectbox("Inteligência", MATRIZ_PADRAO, index=3)
    s_b = ca1.selectbox("Sabedoria", MATRIZ_PADRAO, index=4)
    ca_b = ca2.selectbox("Carisma", MATRIZ_PADRAO, index=5)

    validado = len(set([f_b, d_b, c_b, i_b, s_b, ca_b])) == 6
    if not validado: st.error("⚠️ Não repita os números nos atributos!")

# --- 5. GERAÇÃO ---
if st.button("🔥 Gerar e Baixar PDF") and validado:
    with st.spinner("Processando..."):
        prompt = f"Gere APENAS um JSON para D&D 5e: Raça {raca_sel}, Classe {classe_sel} ({sub_sel}). Nome: {nome_input if nome_input else 'Temático'}. JSON keys: 'nome', 'historia'."
        
        try:
            response = model.generate_content(prompt)
            # Limpeza do JSON
            texto = response.text.strip().replace('```json', '').replace('```', '')
            extra = json.loads(texto)
            
            prof = calc_prof(nivel_sel)
            mod_con = calc_mod(c_b)
            hp = CLASSES_DND[classe_sel]["dado"] + mod_con + ((nivel_sel-1) * (CLASSES_DND[classe_sel]["dado"] // 2 + 1 + mod_con))

            dados_pdf = {
                "Front_Character Name": extra.get("nome", "Herói"),
                "Front_Race": raca_sel,
                "Front_Level": str(nivel_sel),
                "Front_Alignment": tend_sel,
                "Front_Background": ant_sel,
                "Front_Archetype": sub_sel,
                "Front_Proficiency": f"+{prof}",
                "Front_Str Score": str(f_b), "Front_Str Mod": f"{calc_mod(f_b):+}",
                "Front_Dex Score": str(d_b), "Front_Dex Mod": f"{calc_mod(d_b):+}",
                "Front_Con Score": str(c_b), "Front_Con Mod": f"{calc_mod(c_b):+}",
                "Front_Int Score": str(i_b), "Front_Int Mod": f"{calc_mod(i_b):+}",
                "Front_Wis Score": str(s_b), "Front_Wis Mod": f"{calc_mod(s_b):+}",
                "Front_Cha Score": str(ca_b), "Front_Cha Mod": f"{calc_mod(ca_b):+}",
                "Front_Max HP": str(hp), "Front_AC": str(10 + calc_mod(d_b)), "Front_Initiative": f"{calc_mod(d_b):+}"
            }

            # Preenchimento do PDF
            reader = PdfReader(f"modelos/{CLASSES_DND[classe_sel]['pdf']}")
            writer = PdfWriter()
            writer.add_page(reader.pages[0])
            writer.update_page_form_field_values(writer.pages[0], dados_pdf)
            
            saida = "Ficha_DND.pdf"
            with open(saida, "wb") as f:
                writer.write(f)
            
            st.success("Ficha Pronta!")
            with open(saida, "rb") as f:
                st.download_button("📥 Baixar PDF", f, file_name=f"Ficha_{extra.get('nome','Heroi')}.pdf")

        except Exception as e:
            st.error(f"Ocorreu um problema: {e}")
