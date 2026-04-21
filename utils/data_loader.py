import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    """Retorna a engine de conexão com o banco de dados."""
    db_url = None
    
    # 1. Tenta pegar dos secrets do Streamlit (Produção)
    try:
        # Tenta formatos comuns de secrets
        if "postgres" in st.secrets:
            db_url = st.secrets.postgres.get("url")
        elif "POSTGRES_URL" in st.secrets:
            db_url = st.secrets["POSTGRES_URL"]
    except Exception:
        pass
    
    # 2. Fallback para o .env (Local)
    if not db_url:
        db_url = os.getenv("POSTGRES_URL")
    
    if not db_url:
        st.error("⚠️ Configuração de Banco de Dados não encontrada! (Verifique Secrets ou .env)")
        st.stop()
        
    engine = create_engine(db_url)
    
    # Configura o padrão de data brasileiro na conexão
    with engine.connect() as conn:
        conn.execute(text("SET datestyle TO 'ISO, DMY'"))
        conn.commit()
        
    return engine

@st.cache_data
def load_query(query_name, params=None):
    """
    Executa uma query no banco e retorna um DataFrame.
    Não usamos try-except aqui para evitar que erros de conexão sejam salvos no cache.
    """
    engine = get_engine()
    if engine is None:
        return pd.DataFrame()
        
    with engine.connect() as conn:
        df = pd.read_sql(text(query_name), conn, params=params)
        return df

def format_currency(val):
    """Formata valor para Real (R$)."""
    if val >= 1_000_000:
        return f"R$ {val/1_000_000:.2f} Mi"
    elif val >= 1_000:
        return f"R$ {val/1_000:.2f} Mil"
    else:
        return f"R$ {val:.2f}"

def apply_plotly_theme(fig):
    """
    Aplica transparência e fontes profissionais.
    Os gráficos seguirão o tema do Streamlit (Claro/Escuro) automaticamente.
    """
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_family="Roboto, sans-serif",
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="right", 
            x=1
        ),
        margin=dict(t=20, b=20, l=20, r=20),
        hoverlabel=dict(font_size=12, font_family="Roboto")
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.1)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.1)')
    return fig

# Cores oficiais
COLORS = {
    "primary": "#00509E", # Azul Mais Vibrante
    "accent": "#FFD700",  # Ouro (Gold Yellow)
    "neutral": "#666666", # Cinza
    "bg_light": "#F8F9FA",
    "palette": ["#003366", "#FFD700", "#666666", "#00509E", "#FFC300", "#999999"]
}
