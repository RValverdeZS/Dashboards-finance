import streamlit as st
import pandas as pd
from utils.data_loader import load_query, format_currency, COLORS
from utils.ui_components import apply_common_styles, show_sidebar_header

st.set_page_config(page_title="Previsões Financeiras", layout="wide")

# --- ESTILIZAÇÃO E SEGURANÇA ---
apply_common_styles()
from utils.ui_components import check_password
if not check_password():
    st.stop()

show_sidebar_header()

st.title("📜 Gestão de Previsões Financeiras")

# --- CARREGAMENTO DE DADOS ---
df_kpi = load_query("SELECT * FROM v_dashboard_kpis_contrato -- force_ref_v2")
df_pagar = load_query("SELECT * FROM v_dashboard_pagamentos_projetados -- force_ref_v2")
df_resgates = load_query("SELECT * FROM v_dashboard_programacao_resgates -- force_ref_v2")

if df_kpi.empty and df_pagar.empty and df_resgates.empty:
    st.warning("⚠️ Nenhum dado encontrado ou erro na conexão com o banco de dados.")
    st.stop()

# --- KPIs de Custo / Previsão (Reorganizados conforme solicitação) ---
if not df_kpi.empty:
    kpi = df_kpi.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Custo Total Previsto", format_currency(kpi['custo_total_previsto']))
    c2.metric("Custo pago",          format_currency(kpi['custo_pago']))
    pct_pago = (kpi['pct_custo_pago'] * 100)
    c3.metric("% pago",              f"{pct_pago:.1f}%")
    c4.metric("Valor do Contrato",   format_currency(kpi['valor_contrato']))

st.markdown("---")

# --- LINHA 1: NFs + RESGATES + GASTOS (Grid otimizado) ---
col_nf, col_res, col_gas = st.columns([1.5, 1.5, 1])

with col_nf:
    st.markdown("#### Últimas NFs Incluídas")
    if not df_pagar.empty:
        df_display = df_pagar[['fornecedor', 'nf', 'observacoes', 'valor', 'data_evento', 'data_registro', 'hora_registro']]
        df_display = df_display.sort_values(['data_registro', 'hora_registro'], ascending=False)
        st.dataframe(
            df_display.drop(columns=['data_registro', 'hora_registro']),
            column_config={"valor": st.column_config.NumberColumn("Valor", format="R$ %.2f")},
            width='stretch',
            hide_index=True,
            height=280
        )
    else:
        st.info("Nenhuma NF encontrada.")

with col_res:
    st.markdown("#### Programação de Resgates")
    if not df_resgates.empty:
        df_resgates['data_segunda'] = pd.to_datetime(df_resgates['data_segunda'])
        df_res_display = df_resgates[['semana_label', 'total_pagar', 'necessidade_resgate']]
        # Simplifica nomes para caber em tela compacta
        df_res_display.columns = ['Semana', 'A Pagar', 'Resgate']
        st.dataframe(
            df_res_display,
            column_config={
                "A Pagar": st.column_config.NumberColumn("Pagar", format="R$ %.2f"),
                "Resgate": st.column_config.NumberColumn("Resgate", format="R$ %.2f")
            },
            width='stretch',
            hide_index=True,
            height=280
        )
    else:
        st.info("Nenhum dado de resgate disponível.")

with col_gas:
    st.markdown("#### Gastos no Período")
    if not df_pagar.empty:
        df_pagar_gas = df_pagar.copy()
        df_pagar_gas['data_evento'] = pd.to_datetime(df_pagar_gas['data_evento'], errors='coerce').dropna()
        
        meses_df = (
            df_pagar_gas.assign(
                mes_label=df_pagar_gas['data_evento'].dt.strftime('%Y-%m'),
                mes_display=df_pagar_gas['data_evento'].dt.strftime('%m/%Y')
            )[['mes_label', 'mes_display']]
            .drop_duplicates()
            .sort_values('mes_label')
        )
        
        if not meses_df.empty:
            opcoes_display = meses_df['mes_display'].tolist()
            mes_sel = st.selectbox("Mês", opcoes_display, index=len(opcoes_display)-1, key="f_mes_g", label_visibility="collapsed")
            mes_label = meses_df.loc[meses_df['mes_display'] == mes_sel, 'mes_label'].values[0]
            
            df_filtrado = df_pagar_gas[df_pagar_gas['data_evento'].dt.strftime('%Y-%m') == mes_label].copy()
            df_filtrado['sem'] = df_filtrado['data_evento'].dt.day.apply(lambda d: f"{(d-1)//7 + 1}ª Sem")
            
            df_gastos = df_filtrado.groupby('sem')['valor'].sum().reindex([f"{i}ª Sem" for i in range(1,5)]).fillna(0).reset_index()
            df_gastos.columns = ['Semana', 'Valor']
            
            st.dataframe(
                df_gastos,
                column_config={"Valor": st.column_config.NumberColumn("Total", format="R$ %.2f")},
                width='stretch',
                hide_index=True,
                height=220
            )

st.markdown("---")

# --- LINHA 2: EXPANSORES ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Contas por categoria")
    if not df_pagar.empty:
        df_cat = df_pagar.groupby('categoria')['valor'].sum().sort_values(ascending=False).reset_index()
        for _, row in df_cat.iterrows():
            with st.expander(f"{row['categoria']} — {format_currency(row['valor'])}"):
                df_sub = df_pagar[df_pagar['categoria'] == row['categoria']]
                df_sub_group = df_sub.groupby('fornecedor')['valor'].sum().sort_values(ascending=False).reset_index()
                st.dataframe(df_sub_group, width='stretch', hide_index=True)

with col2:
    st.markdown("#### Contas por fornecedor")
    if not df_pagar.empty:
        df_forn_sum = df_pagar.groupby('fornecedor')['valor'].sum().sort_values(ascending=False).reset_index()
        for _, f_row in df_forn_sum.iterrows():
            with st.expander(f"{f_row['fornecedor']} — {format_currency(f_row['valor'])}"):
                df_f_det = df_pagar[df_pagar['fornecedor'] == f_row['fornecedor']][['nf', 'valor', 'data_evento']]
                st.dataframe(df_f_det.sort_values('data_evento'), width='stretch', hide_index=True)
