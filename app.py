import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader, PdfWriter
import json
import math

# --- CONFIGURAÇÃO DA IA ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- BANCO DE DADOS COMPLETO (RAÇAS E CLASSES) ---
# Incluindo PHB, Xanathar, Tasha e Mordenkainen
RACAS_COMPLETAS = [
    # Livro do Jogador (PHB)
    "Anão (Colina)", "Anão (Montanha)", "Elfo (Alto)", "Elfo (Floresta)", "Elfo (Drow)",
    "Halfling (Pés Leves)", "Halfling (Robusto)", "Humano", "Humano (Variante)",
    "Draconato", "Gnomo (Floresta)", "Gnomo (Rocha)", "Meio-Elfo", "Meio-Orc", "Tiefling",
    # Xanathar / Tasha / Mordenkainen (MPMM)
    "Aasimar", "Aarakocra", "Changeling", "Elfo (Eladrin)", "Elfo (Shadar-kai)", 
    "Elfo (Marinho)", "Firbolg", "Genasi (Ar)", "Genasi (Terra)", "Genasi (Fogo)", 
    "Genasi (Água)", "Githyanki", "Githzerai", "Goliath", "Harengon", "Kenku", 
    "Lizardfolk", "Minotauro", "Satir", "Tabaxi", "Tortle", "Tritão", "Yuan-ti"
]

CLASSES_DND = {
    "Bárbaro": {"dado": 12, "pdf": "DnD 5e - Ficha - Bárbaro - Editável.pdf", 
                "subs": ["Berserker", "Totêmico", "Zelote", "Guardião Ancestral", "Arauto da Tempestade", "Besta", "Magia Selvagem"]},
    "Bardo": {"dado": 8, "pdf": "DnD 5e - Ficha - Bardo - Editável.pdf", 
              "subs": ["Saber", "Valor", "Glamour", "Espadas", "Sussurros", "Eloquência", "Criação"]},
    "Bruxo": {"dado": 8, "pdf": "DnD 5e - Ficha - Bruxo - Editável.pdf", 
              "subs": ["Arquifada", "Infernal", "Grande Antigo", "Celestial", "Lâmina Maldita (Hexblade)", "O Gênio", "O Profundo"]},
    "Clérigo": {"dado": 8, "pdf": "DnD 5e - Ficha - Clérigo - Editável.pdf", 
                "subs": ["Vida", "Luz", "Guerra", "Domínio da Forja", "Domínio da Sepultura", "Ordem", "Paz", "Crepúsculo"]},
    "Druida": {"dado": 8, "pdf": "DnD 5e - Ficha - Druída - Editável.pdf", 
               "subs": ["Terra", "Lua", "Sonhos", "Pastor", "Esporos", "Estrelas", "Fogo Selvagem"]},
    "Feiticeiro": {"dado": 6, "pdf": "DnD 5e - Ficha - Feiticeiro - Editável.pdf", 
                   "subs": ["Dracônica", "Magia Selvagem", "Tempestade", "Sombra", "Alma Divina", "Mente Aberrante", "Alma Relojoeira"]},
    "Guerreiro": {"dado": 10, "pdf": "DnD 5e - Ficha - Guerreiro - Editável.pdf", 
                  "subs": ["Campeão", "Mestre de Batalha", "Cavaleiro Arcano", "Arqueiro Arcano", "Samurai", "Cavaleiro Rúnico", "Guerreiro Psiônico"]},
    "Ladino": {"dado": 8, "pdf": "DnD 5e - Ficha - Ladino - Editável.pdf", 
               "subs": ["Assassino", "Gatuno", "Trapaceiro Arcano", "Inquisitivo", "Espadachim", "Fantasma", "Lâmina Psíquica"]},
    "Mago": {"dado": 6, "pdf": "DnD 5e - Ficha - Mago - Editável.pdf", 
             "subs": ["Abjuração", "Evocação", "Adivinhação", "Necromancia", "Magia de Guerra", "Lâmina Cantante", "Ordem dos Escribas"]},
    "Monge": {"dado": 8, "pdf": "DnD 5e - Ficha - Monge - Editável.pdf", 
              "subs": ["Mão Aberta", "Sombras", "Kensei", "Mestre Embriagado", "Misericórdia", "Eu Astral"]},
    "Paladino": {"dado": 10, "pdf": "DnD 5e - Ficha - Paladino - Editável.pdf", 
                 "subs": ["Devoção", "Vingança", "Anciões", "Conquista", "Redenção", "Glória", "Vigilância"]},
    "Patrulheiro": {"dado": 10, "pdf": "DnD 5e - Ficha - Patrulheiro - Editável.pdf", 
                    "subs": ["Caçador", "Mestre das Bestas", "Perseguidor Sombrio", "Andarilho do Horizonte", "Guardião do Enxame", "Guardião de Dracos"]}
}

TENDENCIAS = ["Leal e Bom", "Neutro e Bom", "Caótico e Bom", "Leal e Neutro", "Neutro", "Caótico e Neutro", "Leal e Mau", "Neutro e Mau", "Caótico e Mau"]
ANTECEDENTES = ["Acólito", "Charlatão", "Criminoso", "Entretenimento", "Herói do Povo", "Artesão de Guilda", "Eremita", "Nobre", "Forasteiro", "Sábio", "Marinheiro", "Soldado", "Órfão"]
MATRIZ_PADRAO = [15, 14, 13, 12, 10, 8]

# --- FUNÇÕES ---
def calc_mod(v): return math.floor((v - 10) / 2)
def calc_prof(n): return math.ceil(1 + (n / 4))

# --- INTERFACE ---
st.set_page_config(page_title="D&D 5e Full Generator", layout="wide")
st.title("🧙‍♂️ Gerador de Personagens D&D 5e (Livro Base + Xanathar + Tasha)")

col1, col2 = st.columns(2)

with col1:
    st.header("1. Identidade")
    tipo_nome = st.radio("Nome:", ["Eu escrevo", "IA sugere"])
    nome_input = st.text_input("Escreva o nome:") if tipo_nome == "Eu escrevo" else ""
    
    raca_sel = st.selectbox("Raça (Todos os Livros)", RACAS_COMPLETAS)
    classe_sel = st.selectbox("Classe", list(CLASSES_DND.keys()))
    sub_sel = st.selectbox("Subclasse (Arquétipo)", CLASSES_DND[classe_sel]["subs"])
    nivel_sel = st.slider("Nível", 1, 20, 1)
    tend_sel = st.selectbox("Tendência", TENDENCIAS)
    ant_sel = st.selectbox("Antecedente", ANTECEDENTES)

with col2:
    st.header("2. Atributos (Matriz Padrão)")
    st.warning("Cada valor só pode ser usado uma vez: 15, 14, 13, 12, 10, 8")
    c1, c2 = st.columns(2)
    f_b = c1.selectbox("Força", MATRIZ_PADRAO, index=0)
    d_b = c2.selectbox("Destreza", MATRIZ_PADRAO, index=1)
    c_b = c1.selectbox("Constituição", MATRIZ_PADRAO, index=2)
    i_b = c2.selectbox("Inteligência", MATRIZ_PADRAO, index=3)
    s_b = c1.selectbox("Sabedoria", MATRIZ_PADRAO, index=4)
    ca_b = c2.selectbox("Carisma", MATRIZ_PADRAO, index=5)

    validado = len(set([f_b, d_b, c_b, i_b, s_b, ca_b])) == 6
    if not validado: st.error("⚠️ Erro: Não repita números nos atributos!")

# --- GERAÇÃO DO PDF ---
if st.button("🔥 Gerar e Baixar PDF") and validado:
    with st.spinner("IA processando as regras dos livros..."):
        prompt = f"Crie um personagem D&D 5e: {raca_sel} {classe_sel} ({sub_sel}). Tendência: {tend_sel}. Antecedente: {ant_sel}. {f'Nome: {nome_input}' if nome_input else 'Gere um nome épico.'} Retorne apenas JSON: {{'nome': '...', 'historia': '...'}}"
        
        response = model.generate_content(prompt)
        extra = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
        
        prof = calc_prof(nivel_sel)
        mod_con = calc_mod(c_b)
        hp = CLASSES_DND[classe_sel]["dado"] + mod_con + ((nivel_sel-1) * (CLASSES_DND[classe_sel]["dado"] // 2 + 1 + mod_con))

        campos = {
            "Front_Character Name": extra["nome"], "Front_Race": raca_sel, "Front_Level": str(nivel_sel),
            "Front_Alignment": tend_sel, "Front_Background": ant_sel, "Front_Archetype": sub_sel,
            "Front_Proficiency": f"+{prof}",
            "Front_Str Score": str(f_b), "Front_Str Mod": f"{calc_mod(f_b):+}",
            "Front_Dex Score": str(d_b), "Front_Dex Mod": f"{calc_mod(d_b):+}",
            "Front_Con Score": str(c_b), "Front_Con Mod": f"{calc_mod(c_b):+}",
            "Front_Int Score": str(i_b), "Front_Int Mod": f"{calc_mod(i_b):+}",
            "Front_Wis Score": str(s_b), "Front_Wis Mod": f"{calc_mod(s_b):+}",
            "Front_Cha Score": str(ca_b), "Front_Cha Mod": f"{calc_mod(ca_b):+}",
            "Front_Max HP": str(hp), "Front_AC": str(10 + calc_mod(d_b)), "Front_Initiative": f"{calc_mod(d_b):+}"
        }

        try:
            reader = PdfReader(f"modelos/{CLASSES_DND[classe_sel]['pdf']}")
            writer = PdfWriter()
            writer.add_page(reader.pages[0])
            writer.update_page_form_field_values(writer.pages[0], campos)
            
            output = f"Ficha_{extra['nome']}.pdf"
            with open(output, "wb") as f: writer.write(f)
            st.success(f"Ficha de {extra['nome']} gerada!")
            with open(output, "rb") as f: st.download_button("📥 Baixar PDF", f, file_name=output)
        except Exception as e: st.error(f"Erro ao abrir PDF. Verifique a pasta 'modelos'.")
