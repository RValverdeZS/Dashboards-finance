import streamlit as st
import plotly.express as px
from utils.data_loader import load_query, format_currency, apply_plotly_theme, COLORS
from utils.ui_components import apply_common_styles, show_sidebar_header

st.set_page_config(page_title="Gestão de Pagamentos", layout="wide")

# --- ESTILIZAÇÃO E SEGURANÇA ---
apply_common_styles()
from utils.ui_components import check_password
if not check_password():
    st.stop()

show_sidebar_header()

st.title("📊 Gestão de Pagamentos e Transferências")

# --- FILTROS COMPACTOS ---
with st.expander("🔍 Filtros de Busca", expanded=False):
    col_f1, col_f2, col_f3 = st.columns([1.5, 1.5, 1])
    with col_f1:
        fornecedor_filter = st.text_input("Filtrar por Fornecedor")
    with col_f2:
        df_cats = load_query("SELECT DISTINCT categoria FROM v_dashboard_pagamentos_realizados")
        categoria_selected = st.selectbox("Filtrar por Categoria", ["Todas"] + list(df_cats['categoria']))
    with col_f3:
        # Espaço reservado ou filtro extra de data se necessário
        st.write("")

# --- CARREGAMENTO DE DADOS ---
df = load_query("SELECT * FROM v_dashboard_pagamentos_realizados")

if df.empty:
    st.warning("⚠️ Nenhum dado encontrado para os filtros selecionados ou erro na conexão.")
    st.stop()

if fornecedor_filter:
    df = df[df['fornecedor'].str.contains(fornecedor_filter, case=False, na=False)]
if categoria_selected != "Todas":
    df = df[df['categoria'] == categoria_selected]

# --- LAYOUT DASHBOARD COMPACTO ---
if df.empty:
    st.info("💡 Não há registros para os filtros atuais.")
else:
    # Proporção [1, 2.2] dá muito mais espaço horizontal para a tabela
    c1, c2 = st.columns([1, 2.2])

    with c1:
        st.markdown("### Resumo por Categoria")
        df_cat_group = df.groupby('categoria')['valor'].sum().reset_index()
        
        total_valor = df_cat_group['valor'].sum()
        if total_valor > 0:
            import pandas as pd
            df_cat_group['pct'] = df_cat_group['valor'] / total_valor
            df_outros = df_cat_group[df_cat_group['pct'] < 0.02]
            if not df_outros.empty:
                valor_outros = df_outros['valor'].sum()
                df_cat_group = df_cat_group[df_cat_group['pct'] >= 0.02]
                new_row = pd.DataFrame({'categoria': ['OUTROS'], 'valor': [valor_outros]})
                df_cat_group = pd.concat([df_cat_group, new_row], ignore_index=True)

        fig_cat = px.pie(
            df_cat_group, 
            values='valor', 
            names='categoria', 
            hole=.6,
            color_discrete_sequence=COLORS['palette']
        )
        fig_cat.update_layout(
            showlegend=True,
            legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5),
            margin=dict(t=10, b=10, l=0, r=0),
            height=350
        )
        st.plotly_chart(apply_plotly_theme(fig_cat), use_container_width=True)

        st.markdown("---")
        
        st.markdown("### Top 10 Fornecedores")
        df_forn = df[df['fornecedor'] != 'Transferência / Transf. entre Contas']
        df_forn_group = df_forn.groupby('fornecedor')['valor'].sum().sort_values(ascending=False).head(10).reset_index()
        
        fig_forn = px.bar(
            df_forn_group, 
            x='valor', 
            y='fornecedor', 
            orientation='h',
            color_discrete_sequence=[COLORS['primary']],
            labels={'valor': 'Total (R$)', 'fornecedor': 'Fornecedor'}
        )
        fig_forn.update_layout(
            yaxis={'categoryorder':'total ascending'}, 
            margin=dict(t=0, b=10, l=0, r=10),
            height=350
        )
        st.plotly_chart(apply_plotly_theme(fig_forn), use_container_width=True)

    with c2:
        st.markdown("### Detalhamento dos Pagamentos")
        # Altura aumentada para aproveitar o espaço vertical ao lado dos dois gráficos
        st.dataframe(
            df[['data_evento', 'fornecedor', 'valor', 'categoria', 'nf']].sort_values(by='data_evento', ascending=False), 
            width='stretch', 
            height=850, 
            hide_index=True
        )

    # --- RODAPÉ COMPACTO ---
    st.markdown("---")
    sc1, sc2, sc3 = st.columns([1.5, 1, 1.5])
    with sc2:
        st.markdown("<h4 style='text-align: center; margin-bottom: 0;'>Distribuições por Sócio</h4>", unsafe_allow_html=True)
        df_socio = df[df['socio'] != 'Operacional'].groupby('socio')['valor'].sum().reset_index()
        if not df_socio.empty:
            fig_socio = px.pie(
                df_socio, 
                values='valor', 
                names='socio', 
                hole=.4,
                color='socio',
                color_discrete_map={
                    'ENOTEC': COLORS['primary'],
                    'LFM': COLORS['accent'],
                    'COBRAPE': COLORS['neutral']
                }
            )
            fig_socio.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250, showlegend=True)
            st.plotly_chart(apply_plotly_theme(fig_socio), use_container_width=True)
