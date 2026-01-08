import streamlit as st
import google.generativeai as genai
import json

# Certifique-se de que a chave está salva nos Secrets do Streamlit!
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3-flash-preview')

st.title("🎲 D&D 5e Auto-Ficha (LDJ, Tasha, Xanathar)")

# Novos campos de seleção
col1, col2 = st.columns(2)
with col1:
    classe = st.selectbox("Classe", ["Guerreiro", "Monge", "Mago", "Ladino", "Bardo", "Bruxo", "Clérigo", "Druida", "Bárbaro", "Feiticeiro"])
with col2:
    # Lista ampliada com raças de Xanathar e Tasha
    raca = st.selectbox("Raça", ["Anão", "Elfo", "Humano", "Halfling", "Draconato", "Gnomo", "Meio-Elfo", "Meio-Orc", "Tiefling", "Tabaxi", "Tritão", "Aasimar"])

nivel = st.slider("Nível do Personagem", 1, 20, 1)

if st.button("✨ Gerar Personagem com Gemini 3 Flash"):
    # Prompt detalhado para buscar regras específicas dos livros mencionados
    prompt = f"""
    Gere uma ficha de D&D 5e para um {classe} {raca} nível {nivel}.
    Considere as regras e variantes dos livros: Player's Handbook, Tasha's Cauldron of Everything e Xanathar's Guide to Everything.
    Retorne APENAS um JSON puro com as chaves: 
    "nome", "raca", "for", "des", "con", "int", "sab", "car", "tracos_raciais", "habilidades_classe".
    """
    
    try:
        response = model.generate_content(prompt)
        # Limpa e carrega o JSON
        texto_limpo = response.text.replace('```json', '').replace('```', '').strip()
        dados = json.loads(texto_limpo)
        
        st.subheader(f"Personagem: {dados['nome']}")
        st.write(f"**Raça:** {dados['raca']} | **Classe:** {classe} Nível {nivel}")
        
        # Exibe os traços buscados pela IA
        st.info(f"**Traços Raciais ({raca}):** {dados['tracos_raciais']}")
        
        # Aqui você chamaria a função de preencher o PDF que configuramos antes
        st.success("Dados buscados com sucesso nos livros de regras!")
    except Exception as e:
        st.error(f"Erro ao processar dados da IA: {e}")
