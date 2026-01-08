import streamlit as st
from google import genai
from pypdf import PdfReader, PdfWriter
import json
import math

# --- 1. CONFIGURAÇÃO DO CLIENTE ---
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    MODELO = "gemini-2.0-flash-exp"
except Exception as e:
    st.error(f"Erro na API: {e}")
    st.stop()

# --- 2. BANCO DE DADOS DE REGRAS (PHB + EXPANSÕES) ---
CLASSES_DND = {
    "Guerreiro": {"dado": 10, "pdf": "DnD 5e - Ficha - Guerreiro - Editável.pdf", 
                  "subs": ["Campeão", "Mestre de Batalha", "Cavaleiro Arcano", "Samurai", "Psiônico"]},
    "Mago": {"dado": 6, "pdf": "DnD 5e - Ficha - Mago - Editável.pdf", 
             "subs": ["Evocação", "Abjuração", "Adivinhação", "Lâmina Cantante"]},
    "Ladino": {"dado": 8, "pdf": "DnD 5e - Ficha - Ladino - Editável.pdf", 
               "subs": ["Assassino", "Gatuno", "Trapaceiro Arcano", "Fantasma"]},
    "Bárbaro": {"dado": 12, "pdf": "DnD 5e - Ficha - Bárbaro - Editável.pdf", 
                "subs": ["Berserker", "Totêmico", "Zelote", "Besta"]},
    "Bardo": {"dado": 8, "pdf": "DnD 5e - Ficha - Bardo - Editável.pdf", 
              "subs": ["Saber", "Valor", "Eloquência", "Espadas"]},
    "Clérigo": {"dado": 8, "pdf": "DnD 5e - Ficha - Clérigo - Editável.pdf", 
                "subs": ["Vida", "Guerra", "Tempestade", "Sepultura"]},
    "Paladino": {"dado": 10, "pdf": "DnD 5e - Ficha - Paladino - Editável.pdf", 
                 "subs": ["Devoção", "Vingança", "Glória", "Conquista"]},
    "Patrulheiro": {"dado": 10, "pdf": "DnD 5e - Ficha - Patrulheiro - Editável.pdf", 
                    "subs": ["Caçador", "Mestre das Bestas", "Perseguidor Sombrio"]}
}

RACAS = ["Anão (Montanha)", "Anão (Colina)", "Elfo (Alto)", "Elfo (Floresta)", "Elfo (Shadar-kai)", 
         "Humano", "Draconato", "Tiefling", "Tabaxi", "Goliath", "Aasimar", "Harengon"]

TENDENCIAS = ["Leal e Bom", "Neutro", "Caótico e Bom", "Leal e Neutro", "Caótico e Neutro", "Leal e Mau", "Neutro e Mau", "Caótico e Mau"]
ANTECEDENTES = ["Acólito", "Charlatão", "Criminoso", "Entretenimento", "Herói do Povo", "Nobre", "Forasteiro", "Sábio", "Soldado", "Órfão"]
MATRIZ_PADRAO = [15, 14, 13, 12, 10, 8]

# --- 3. FUNÇÕES ---
def calc_mod(v): return math.floor((v - 10) / 2)
def calc_prof(n): return math.ceil(1 + (n / 4))

# --- 4. INTERFACE ---
st.set_page_config(page_title="D&D AI Builder Pro", layout="wide")
st.title("🛡️ Gerador D&D 5e Completo (IA + Equipamento)")

c1, c2 = st.columns(2)

with c1:
    st.header("Identidade")
    tipo_nome = st.radio("Nome:", ["Eu escrevo", "IA gera"])
    nome_input = st.text_input("Escreva o nome:") if tipo_nome == "Eu escrevo" else ""
    raca_sel = st.selectbox("Raça", RACAS)
    classe_sel = st.selectbox("Classe", list(CLASSES_DND.keys()))
    sub_sel = st.selectbox("Subclasse", CLASSES_DND[classe_sel]["subs"])
    nivel_sel = st.slider("Nível", 1, 20, 1)
    tend_sel = st.selectbox("Tendência", TENDENCIAS)
    ant_sel = st.selectbox("Antecedente", ANTECEDENTES)

with c2:
    st.header("Atributos (Matriz Padrão)")
    ca1, ca2 = st.columns(2)
    f_b = ca1.selectbox("Força", MATRIZ_PADRAO, index=0)
    d_b = ca2.selectbox("Destreza", MATRIZ_PADRAO, index=1)
    c_b = ca1.selectbox("Constituição", MATRIZ_PADRAO, index=2)
    i_b = ca2.selectbox("Inteligência", MATRIZ_PADRAO, index=3)
    s_b = ca1.selectbox("Sabedoria", MATRIZ_PADRAO, index=4)
    ca_b = ca2.selectbox("Carisma", MATRIZ_PADRAO, index=5)
    validado = len(set([f_b, d_b, c_b, i_b, s_b, ca_b])) == 6

# --- 5. GERAÇÃO ---
if st.button("🎲 Criar Personagem Completo") and validado:
    with st.spinner("IA selecionando armas e equipamentos..."):
        prompt = f"""
        Gere APENAS um JSON para D&D 5e: Raça {raca_sel}, Classe {classe_sel} ({sub_sel}), Nível {nivel_sel}, Antecedente {ant_sel}.
        Nome: {nome_input if nome_input else 'Temático'}.
        Determine o equipamento inicial (armas, armaduras, kits) seguindo o PHB.
        Retorne JSON: {{"nome": "...", "historia": "...", "equipamento": "lista de itens separados por vírgula"}}
        """
        
        try:
            response = client.models.generate_content(model=MODELO, contents=prompt)
            texto_json = response.text.strip().replace('```json', '').replace('```', '')
            extra = json.loads(texto_json)
            
            prof = calc_prof(nivel_sel)
            hp = CLASSES_DND[classe_sel]["dado"] + calc_mod(c_b) + ((nivel_sel-1) * (CLASSES_DND[classe_sel]["dado"]//2 + 1 + calc_mod(c_b)))

            dados_pdf = {
                "Front_Character Name": extra["nome"],
                "Front_Race": raca_sel,
                "Front_Level": str(nivel_sel),
                "Front_Archetype": sub_sel,
                "Front_Alignment": tend_sel,
                "Front_Background": ant_sel,
                "Front_Proficiency": f"+{prof}",
                "Front_Str Score": str(f_b), "Front_Str Mod": f"{calc_mod(f_b):+}",
                "Front_Dex Score": str(d_b), "Front_Dex Mod": f"{calc_mod(d_b):+}",
                "Front_Con Score": str(c_b), "Front_Con Mod": f"{calc_mod(c_b):+}",
                "Front_Int Score": str(i_b), "Front_Int Mod": f"{calc_mod(i_b):+}",
                "Front_Wis Score": str(s_b), "Front_Wis Mod": f"{calc_mod(s_b):+}",
                "Front_Cha Score": str(ca_b), "Front_Cha Mod": f"{calc_mod(ca_b):+}",
                "Front_Max HP": str(hp),
                "Front_AC": str(10 + calc_mod(d_b)),
                "Front_Initiative": f"{calc_mod(d_b):+}",
                # PREENCHE O EQUIPAMENTO NO PDF
                "Back_Additional Features & Traits": extra["equipamento"] # Campo comum para itens em PDFs editáveis
            }

            # Localiza e preenche o PDF
            caminho_pdf = f"modelos/{CLASSES_DND[classe_sel]['pdf']}"
            reader = PdfReader(caminho_pdf)
            writer = PdfWriter()
            writer.add_page(reader.pages[0])
            writer.update_page_form_field_values(writer.pages[0], dados_pdf)
            
            nome_arq = f"Ficha_{extra['nome'].replace(' ', '_')}.pdf"
            with open(nome_arq, "wb") as f:
                writer.write(f)
            
            st.success(f"✅ Ficha de {extra['nome']} gerada com armas e equipamentos!")
            with open(nome_arq, "rb") as f:
                st.download_button("📥 Baixar Ficha PDF", f, file_name=nome_arq)

        except Exception as e:
            st.error(f"Erro ao gerar ficha: {e}")
