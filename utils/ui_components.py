import streamlit as st
import os
from utils.data_loader import COLORS

def apply_common_styles():
    """
    Aplica estilos CSS usando variáveis nativas do Streamlit.
    Isso permite que o app siga o tema do navegador (Light/Dark) automaticamente.
    """
    st.markdown(f"""
    <style>
        /* Estilo para Cartões de Métricas - Adaptativo */
        [data-testid="stMetric"], .stMetric {{
            background-color: var(--secondary-background-color) !important;
            border-radius: 12px !important;
            border-left: 5px solid {COLORS['accent']} !important;
            padding: 15px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        }}
        
        /* Sidebar mantém a identidade visual (Azul Vibrante) */
        [data-testid="stSidebar"], [data-testid="stSidebarNav"] {{
            background-color: {COLORS['primary']} !important;
        }}
        [data-testid="stSidebar"] * {{
            color: white !important;
        }}
        
        /* Ajuste de transição para uma troca suave de tema */
        .stApp {{
            transition: background-color 0.3s ease, color 0.3s ease;
        }}
    </style>
    """, unsafe_allow_html=True)

def show_sidebar_header():
    """Exibe o logo no sidebar."""
    LOGO_PATH = "dashboards/templates/LOGO CONSÓRCIO LFM ENOTEC COBRAPE V2_POSITIVO.png"
    if os.path.exists(LOGO_PATH):
        st.sidebar.image(LOGO_PATH, use_container_width=True)
    else:
        st.sidebar.title("Consórcio 7B")

def check_password():
    """Retorna True se o usuário inseriu a senha correta."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    # Exibe formulário de login
    st.markdown("""
        <style>
        .login-box {
            max-width: 400px;
            padding: 2rem;
            margin: 5rem auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.title("🔒 Acesso Restrito")
        password = st.text_input("Digite a senha para acessar o dashboard:", type="password")
        
        # Tenta pegar a senha correta (Secrets -> .env -> Fallback fixo)
        try:
            correct_password = st.secrets["auth"]["password"]
        except:
            correct_password = os.getenv("DASHBOARD_PASSWORD", "7b_consorcio_2024")

        if st.button("Entrar"):
            if password == correct_password:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
        
        st.stop() # Interrompe a execução se não estiver logado
    return False
