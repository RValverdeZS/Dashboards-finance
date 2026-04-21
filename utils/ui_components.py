import streamlit as st
import os
from utils.data_loader import COLORS

def apply_common_styles():
    """
    Aplica estilos CSS para o Modo Compacto e Profissional.
    Otimiza o uso de espaço e reduz tamanhos de fonte.
    """
    st.markdown(f"""
    <style>
        /* Redução de Fontes Globais (Modo Compacto) */
        h1 {{ font-size: 1.8rem !important; margin-bottom: 0.5rem !important; }}
        h2 {{ font-size: 1.4rem !important; margin-bottom: 0.5rem !important; }}
        h3 {{ font-size: 1.1rem !important; margin-bottom: 0.5rem !important; }}
        
        /* Ajuste de Texto em Métricas */
        [data-testid="stMetricValue"] {{ font-size: 1.6rem !important; }}
        [data-testid="stMetricLabel"] {{ font-size: 0.9rem !important; }}
        
        /* Redução da largura da Sidebar */
        [data-testid="stSidebar"] {{
            min-width: 250px !important;
            max-width: 250px !important;
        }}
        
        /* Ocupar mais espaço na tela e reduzir paddings */
        .main .block-container {{
            max-width: 98% !important;
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }}
        
        /* Reduzir o GAP entre colunas e widgets */
        [data-testid="stHorizontalBlock"] {{
            gap: 1rem !important;
        }}

        /* Estilo para Cartões de Métricas Compactos */
        [data-testid="stMetric"], .stMetric {{
            background-color: var(--secondary-background-color) !important;
            border-radius: 8px !important;
            border-left: 4px solid {COLORS['accent']} !important;
            padding: 8px 12px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
        }}
        
        /* Sidebar mantém a identidade visual (Azul Vibrante) */
        [data-testid="stSidebar"], [data-testid="stSidebarNav"] {{
            background-color: {COLORS['primary']} !important;
        }}
        [data-testid="stSidebar"] * {{
            color: white !important;
            font-size: 0.95rem !important;
        }}
        
        /* Ajuste nas tabelas Dataframe para fonte menor */
        .stDataFrame td, .stDataFrame th {{
            font-size: 0.85rem !important;
        }}
    </style>
    """, unsafe_allow_html=True)

def show_sidebar_header():
    """Exibe o logo no sidebar."""
    LOGO_PATH = "dashboards/templates/logo_consorcio.png"
    if os.path.exists(LOGO_PATH):
        st.sidebar.image(LOGO_PATH, width='stretch')

def check_password():
    """Retorna True se o usuário inseriu a senha correta."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    # Exibe formulário de login compacto
    st.markdown("""
        <style>
        .login-box {
            max-width: 350px;
            padding: 1.5rem;
            margin: 4rem auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    cols = st.columns([1, 1.5, 1])
    with cols[1]:
        st.title("🔒 Acesso Restrito")
        password = st.text_input("Senha:", type="password")
        
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
        
        st.stop()
    return False
