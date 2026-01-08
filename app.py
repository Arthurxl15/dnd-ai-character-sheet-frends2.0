import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader, PdfWriter
import json
import math

# Configuração da IA
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3-flash-preview')

def calcular_mod(valor):
    return math.floor((valor - 10) / 2)

def calcular_proficiencia(nivel):
    return math.ceil(1 + (nivel / 4))

# Mapeamento de Dados de Vida (HD) conforme LDJ
DADOS_VIDA = {
    "Bárbaro": 12, "Guerreiro": 10, "Paladino": 10, "Patrulheiro": 10,
    "Clérigo": 8, "Bardo": 8, "Druida": 8, "Ladino": 8, "Monge": 8, "Bruxo": 8,
    "Mago": 6, "Feiticeiro": 6
}

# --- INTERFACE ---
st.title("🛡️ Gerador de Fichas Automático (Regras Oficiais)")

with st.sidebar:
    classe = st.selectbox("Classe", list(DADOS_VIDA.keys()))
    nivel = st.slider("Nível", 1, 20, 1)
    # Atributos Matriz Padrão
    st.write("Atributos Base:")
    forca = st.number_input("Força", 0, 30, 15)
    des = st.number_input("Destreza", 0, 30, 14)
    con = st.number_input("Constituição", 0, 30, 13)
    int_ = st.number_input("Inteligência", 0, 30, 12)
    sab = st.number_input("Sabedoria", 0, 30, 10)
    car = st.number_input("Carisma", 0, 30, 8)

if st.button("✨ Gerar PDF com Cálculos"):
    # Cálculos Automáticos baseados no LDJ
    mod_con = calcular_mod(con)
    pv_max = DADOS_VIDA[classe] + mod_con + ((nivel - 1) * (DADOS_VIDA[classe] // 2 + 1 + mod_con))
    prof = calcular_proficiencia(nivel)
    passiva = 10 + calcular_mod(sab)

    # Dados para preencher o PDF (usando os nomes técnicos internos da sua ficha)
    dados_pdf = {
        "Front_Character Name": "Herói de Teste",
        "Front_Level": str(nivel),
        "Front_Str Score": str(forca),
        "Front_Str Mod": f"{calcular_mod(forca):+}",
        "Front_Dex Score": str(des),
        "Front_Dex Mod": f"{calcular_mod(des):+}",
        "Front_Con Score": str(con),
        "Front_Con Mod": f"{calcular_mod(con):+}",
        "Front_Int Score": str(int_),
        "Front_Int Mod": f"{calcular_mod(int_):+}",
        "Front_Wis Score": str(sab),
        "Front_Wis Mod": f"{calcular_mod(sab):+}",
        "Front_Cha Score": str(car),
        "Front_Cha Mod": f"{calcular_mod(car):+}",
        "Front_Proficiency": f"+{prof}",
        "Front_Max HP": str(pv_max),
        "Front_Passive Perception": str(passiva),
        "Front_AC": str(10 + calcular_mod(des)),
        "Front_Initiative": f"{calcular_mod(des):+}"
    }

    # Lógica de preenchimento (pypdf)
    # [O código de preenchimento do PDF que já usamos entra aqui]
    st.success(f"Cálculos realizados! Vida: {pv_max}, Proficiência: +{prof}")
