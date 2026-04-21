import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.data_loader import load_query, format_currency, apply_plotly_theme, COLORS
from utils.ui_components import apply_common_styles, show_sidebar_header

st.set_page_config(page_title="Recebimentos", layout="wide")

apply_common_styles()
from utils.ui_components import check_password
if not check_password():
    st.stop()
show_sidebar_header()

st.title("💰 Recebimentos")
st.markdown("---")

# --- CARREGAMENTO DE DADOS ---
df_kpi     = load_query("SELECT * FROM v_dashboard_kpis_contrato")
df_receber = load_query("""
    SELECT 
        cr.codigo_lancamento_omie,
        cr.numero_documento_fiscal                            AS nf,
        COALESCE(c.razao_social, c.nome_fantasia, 'N/D')     AS cliente,
        cr.valor_documento                                    AS valor_bruto,
        COALESCE(cr.valor_iss,0)+COALESCE(cr.valor_inss,0)+COALESCE(cr.valor_ir,0) AS impostos,
        cr.valor_documento - (COALESCE(cr.valor_iss,0)+COALESCE(cr.valor_inss,0)+COALESCE(cr.valor_ir,0)) AS valor_liquido,
        cr.data_vencimento,
        cr.data_registro,
        cr.status_titulo
    FROM omie_contas_receber cr
    LEFT JOIN omie_clientes c ON cr.codigo_cliente_fornecedor = c.codigo_cliente_omie
    ORDER BY cr.data_vencimento DESC
""")

if df_kpi.empty and df_receber.empty:
    st.warning("⚠️ Nenhum dado encontrado para Recebimentos.")
    st.stop()

kpi = df_kpi.iloc[0] if not df_kpi.empty else None

# --- KPIs de Recebimento / Faturamento ---
if kpi is not None:
    total_bruto    = df_receber['valor_bruto'].sum() if not df_receber.empty else 0
    total_impostos = df_receber['impostos'].sum() if not df_receber.empty else 0
    total_liquido  = df_receber['valor_liquido'].sum() if not df_receber.empty else 0

    r1, r2, r3 = st.columns(3)
    r1.metric("Valor do Contrato",       format_currency(kpi['valor_contrato']))
    r2.metric("Valor Faturado",          format_currency(kpi['valor_faturado']))
    pct_faturado = (kpi['valor_faturado'] / kpi['valor_contrato'] * 100) if kpi['valor_contrato'] > 0 else 0
    r3.metric("% Faturado",             f"{pct_faturado:.2f}%")

    r4, r5, r6 = st.columns(3)
    r4.metric("Total Amortizado",        format_currency(kpi['total_amortizado']))
    r5.metric("Retenção Performance",    format_currency(kpi['total_retencao_performance']))
    r6.metric("Retenção Seguro",         format_currency(kpi['total_retencao_seguro']))

st.markdown("---")

# --- LINHA 1: WATERFALL + RESUMO POR STATUS ---
col_w, col_s = st.columns([2, 1])

with col_w:
    st.subheader("Composição dos Recebimentos")
    if kpi is not None:
        v_bruto     = kpi['valor_faturado']
        v_amort     = -kpi['total_amortizado']
        v_retencoes = -(kpi['total_retencao_performance'] + kpi['total_retencao_seguro'])
        v_liquido   = v_bruto + v_amort + v_retencoes

        fig = go.Figure(go.Waterfall(
            name="Fluxo", orientation="v",
            measure=["absolute", "relative", "relative", "total"],
            x=["Valor Bruto", "Amortização", "Retenções (Perf/Seg)", "Valor Líquido"],
            textposition="outside",
            text=[format_currency(v_bruto), format_currency(v_amort), format_currency(v_retencoes), format_currency(v_liquido)],
            y=[v_bruto, v_amort, v_retencoes, v_liquido],
            connector={"line": {"color": COLORS['neutral']}},
            decreasing={"marker": {"color": "#ef553b"}},
            increasing={"marker": {"color": "#00cc96"}},
            totals={"marker": {"color": COLORS['primary']}}
        ))
        st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

with col_s:
    st.subheader("Por Status")
    if not df_receber.empty:
        df_status = df_receber.groupby('status_titulo')['valor_bruto'].agg(['sum', 'count']).reset_index()
        df_status.columns = ['Status', 'Valor Total', 'Qtd NFs']
        st.dataframe(
            df_status,
            column_config={"Valor Total": st.column_config.NumberColumn("Valor Total", format="R$ %.2f")},
            use_container_width=True,
            hide_index=True
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Por Fornecedor")
        if not df_receber.empty:
            df_cli = df_receber.groupby('cliente')['valor_bruto'].sum().sort_values(ascending=False).reset_index()
            df_cli.columns = ['Cliente', 'Valor Total']
            st.dataframe(
                df_cli,
                column_config={"Valor Total": st.column_config.NumberColumn("Valor", format="R$ %.2f")},
                use_container_width=True,
                hide_index=True
            )

st.markdown("---")

# --- LINHA 2: TABELA DETALHADA ---
st.subheader("Recebimentos Detalhados por NF")

if not df_receber.empty:
    # Filtro por status
    status_opts = ["Todos"] + sorted(df_receber['status_titulo'].dropna().unique().tolist())
    status_sel  = st.selectbox("Filtrar por Status", status_opts, key="filtro_status_receb")

    df_show = df_receber if status_sel == "Todos" else df_receber[df_receber['status_titulo'] == status_sel]

    st.dataframe(
        df_show,
        column_config={
            "valor_bruto":   st.column_config.NumberColumn("Valor Bruto",  format="R$ %.2f"),
            "impostos":      st.column_config.NumberColumn("Impostos",     format="R$ %.2f"),
            "valor_liquido": st.column_config.NumberColumn("Valor Líquido",format="R$ %.2f"),
        },
        use_container_width=True,
        hide_index=True,
        height=400
    )
else:
    st.info("Nenhum dado de recebimento encontrado.")
