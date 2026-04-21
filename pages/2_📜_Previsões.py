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
st.markdown("---")

# --- CARREGAMENTO DE DADOS ---
df_kpi = load_query("SELECT * FROM v_dashboard_kpis_contrato")
df_pagar = load_query("SELECT * FROM v_dashboard_pagamentos_projetados")
df_resgates = load_query("SELECT * FROM v_dashboard_programacao_resgates")

if df_kpi.empty and df_pagar.empty and df_resgates.empty:
    st.warning("⚠️ Nenhum dado encontrado ou erro na conexão com o banco de dados.")
    st.stop()

# --- KPIs de Custo / Previsão ---
if not df_kpi.empty:
    kpi = df_kpi.iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Custo Total Previsto", format_currency(kpi['custo_total_previsto']))
    c2.metric("Custo Total Pago",     format_currency(kpi['custo_pago']))
    c3.metric("Total Adiantado",      format_currency(kpi['total_adiantado']))

    c4, c5, c6 = st.columns(3)
    pct_pago = (kpi['pct_custo_pago'] * 100)
    c4.metric("% Executado (Custo)", f"{pct_pago:.2f}%")
    c5.metric("Retenção Performance", format_currency(kpi['total_retencao_performance']))
    c6.metric("Retenção Seguro",      format_currency(kpi['total_retencao_seguro']))

st.markdown("---")

# --- LINHA 1: NFs + RESGATES + GASTOS (Tabelas compactas no topo) ---
col_nf, col_res, col_gas = st.columns([1.4, 1.4, 0.8])

with col_nf:
    st.subheader("Últimas NFs Incluídas")
    if not df_pagar.empty:
        df_display = df_pagar[['fornecedor', 'nf', 'observacoes', 'valor', 'data_evento', 'data_registro', 'hora_registro']]
        df_display = df_display.sort_values(['data_registro', 'hora_registro'], ascending=False)
        st.dataframe(
            df_display.drop(columns=['data_registro', 'hora_registro']),
            column_config={"valor": st.column_config.NumberColumn("Valor", format="R$ %.2f")},
            use_container_width=True,
            hide_index=True,
            height=320
        )
    else:
        st.info("Nenhuma NF encontrada.")

with col_res:
    st.subheader("Programação de Resgates")
    if not df_resgates.empty:
        df_resgates['data_segunda'] = pd.to_datetime(df_resgates['data_segunda'])
        df_resgates['Ano'] = df_resgates['data_segunda'].dt.year
        df_resgates['Trimestre'] = 'Q' + df_resgates['data_segunda'].dt.quarter.astype(str)
        df_resgates['Mês'] = df_resgates['data_segunda'].dt.strftime('%B')
        df_resgates['Dia'] = df_resgates['data_segunda'].dt.day
        
        df_res_display = df_resgates[['semana_label', 'Ano', 'Trimestre', 'Mês', 'Dia', 'total_pagar', 'necessidade_resgate']]
        df_res_display.columns = ['Semana', 'Ano', 'Trimestre', 'Mês', 'Dia', 'A Pagar', 'Resgate']
        st.dataframe(
            df_res_display,
            column_config={
                "A Pagar": st.column_config.NumberColumn("Valor a Pagar", format="R$ %.2f"),
                "Resgate": st.column_config.NumberColumn("Resgate Necessário", format="R$ %.2f")
            },
            use_container_width=True,
            hide_index=True,
            height=320
        )
    else:
        st.info("Nenhum dado de resgate disponível.")

with col_gas:
    st.subheader("Gastos no Período")
    if not df_pagar.empty:
        df_pagar_gas = df_pagar.copy()
        df_pagar_gas['data_evento'] = pd.to_datetime(df_pagar_gas['data_evento'], errors='coerce')
        df_pagar_gas = df_pagar_gas.dropna(subset=['data_evento'])

        # Label simples como string para evitar problemas com Period
        df_pagar_gas['mes_ano_label'] = df_pagar_gas['data_evento'].dt.strftime('%Y-%m')
        df_pagar_gas['mes_ano_display'] = df_pagar_gas['data_evento'].dt.strftime('%m/%Y')

        meses_df = (
            df_pagar_gas[['mes_ano_label', 'mes_ano_display']]
            .drop_duplicates()
            .sort_values('mes_ano_label')
        )
        opcoes_label = meses_df['mes_ano_label'].tolist()
        opcoes_display = meses_df['mes_ano_display'].tolist()

        idx_default = len(opcoes_display) - 1
        mes_sel_display = st.selectbox(
            "Mês", opcoes_display, index=idx_default,
            key="filtro_mes_gastos", label_visibility="collapsed"
        )
        mes_sel_label = opcoes_label[opcoes_display.index(mes_sel_display)]

        df_filtrado = df_pagar_gas[df_pagar_gas['mes_ano_label'] == mes_sel_label].copy()

        # Recalcula semana do mês em Python (garante consistência)
        # Semana 1: dias 1-8, Semana 2: 9-16, Semana 3: 17-24, Semana 4: 25+
        def semana_do_mes(dia):
            if dia <= 8:   return "1ª Semana"
            if dia <= 16:  return "2ª Semana"
            if dia <= 24:  return "3ª Semana"
            return "4ª Semana"

        df_filtrado['semana_calc'] = df_filtrado['data_evento'].dt.day.apply(semana_do_mes)

        df_gastos = df_filtrado.groupby('semana_calc')['valor'].sum().reset_index()
        df_gastos.columns = ['Semana do Mês', 'Valor']

        # Sempre exibe as 4 semanas, mesmo com valor zero
        todas_semanas = pd.DataFrame({'Semana do Mês': ['1ª Semana', '2ª Semana', '3ª Semana', '4ª Semana']})
        df_gastos = todas_semanas.merge(df_gastos, on='Semana do Mês', how='left').fillna(0)

        total_mes = df_filtrado['valor'].sum()
        st.caption(f"Total em {mes_sel_display}: **{format_currency(total_mes)}** ({len(df_filtrado)} lançamentos)")

        st.dataframe(
            df_gastos,
            column_config={"Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f")},
            use_container_width=True,
            hide_index=True,
            height=240
        )


st.markdown("---")

# --- LINHA 2: EXPANSORES (Categorias e Fornecedores — ficam embaixo) ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Previsão por Categoria")
    if not df_pagar.empty:
        df_cat = df_pagar.groupby('categoria')['valor'].sum().sort_values(ascending=False).reset_index()
        for _, row in df_cat.iterrows():
            with st.expander(f"📁 {row['categoria']} — {format_currency(row['valor'])}"):
                df_sub = df_pagar[df_pagar['categoria'] == row['categoria']]
                df_sub_group = df_sub.groupby('fornecedor')['valor'].sum().sort_values(ascending=False).reset_index()
                st.dataframe(
                    df_sub_group,
                    column_config={"valor": st.column_config.NumberColumn("Valor", format="R$ %.2f")},
                    use_container_width=True,
                    hide_index=True
                )
    else:
        st.info("Nenhuma previsão encontrada.")

with col2:
    st.subheader("Previsão por Fornecedor (Detalhamento)")
    if not df_pagar.empty:
        df_forn_sum = df_pagar.groupby('fornecedor')['valor'].sum().sort_values(ascending=False).reset_index()
        for _, f_row in df_forn_sum.head(15).iterrows():
            with st.expander(f"👤 {f_row['fornecedor']} — {format_currency(f_row['valor'])}"):
                df_f_det = df_pagar[df_pagar['fornecedor'] == f_row['fornecedor']][['nf', 'observacoes', 'valor', 'data_evento', 'origem']]
                st.dataframe(
                    df_f_det.sort_values('data_evento'),
                    column_config={"valor": st.column_config.NumberColumn("Valor", format="R$ %.2f")},
                    use_container_width=True,
                    hide_index=True
                )
    else:
        st.info("Nenhuma previsão encontrada.")
