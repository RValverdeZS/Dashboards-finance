import streamlit as st
from utils.ui_components import apply_common_styles, show_sidebar_header

# Configuração da página
st.set_page_config(
    page_title="Consórcio LFM-ENOTEC-COBRAPE | Hub",
    page_icon="🚀",
    layout="wide",
)

# --- ESTILIZAÇÃO E SEGURANÇA ---
apply_common_styles()
from utils.ui_components import check_password
if not check_password():
    st.stop()

show_sidebar_header()


# --- CONTEÚDO PRINCIPAL (HOME) ---
st.title("🚀 Hub de Inteligência")

st.markdown("---")
c1, c2, c3 = st.columns(3)

with c1:
    st.info("📊 **Pagamentos**\n\nControle de fluxo de caixa realizado, transferências entre contas e divisão por sócios (LFM, ENOTEC, COBRAPE).")

with c2:
    st.info("📜 **Previsões**\n\nPlanejamento de custos futuros, programação de resgates e saldo de caixa necessário para as próximas semanas.")

with c3:
    st.info("💰 **Recebimentos**\n\nAcompanhamento de faturamento, medições, impostos e retenções técnicas (Performance/Seguro).")

st.markdown("---")
