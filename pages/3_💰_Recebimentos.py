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

# --- KPIs de Recebimento (Linha única compacta) ---
if kpi is not None:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Contrato",       format_currency(kpi['valor_contrato']))
    c2.metric("Faturado",       format_currency(kpi['valor_faturado']))
    pct_faturado = (kpi['valor_faturado'] / kpi['valor_contrato'] * 100) if kpi['valor_contrato'] > 0 else 0
    c3.metric("% Faturado",     f"{pct_faturado:.1f}%")
    c4.metric("Amortizado",     format_currency(kpi['total_amortizado']))
    c5.metric("Perf.",          format_currency(kpi['total_retencao_performance']))
    c6.metric("Seguro",         format_currency(kpi['total_retencao_seguro']))

st.markdown("---")

# --- LINHA 1: WATERFALL + STATUS (Grid compacta) ---
col_w, col_s = st.columns([1.8, 1])

with col_w:
    st.markdown("#### Composição dos Recebimentos")
    if kpi is not None:
        v_bruto     = kpi['valor_faturado']
        v_amort     = -kpi['total_amortizado']
        v_retencoes = -(kpi['total_retencao_performance'] + kpi['total_retencao_seguro'])
        v_liquido   = v_bruto + v_amort + v_retencoes

        fig = go.Figure(go.Waterfall(
            name="Fluxo", orientation="v",
            measure=["absolute", "relative", "relative", "total"],
            x=["Bruto", "Amort.", "Retenções", "Líquido"],
            textposition="outside",
            text=[format_currency(v_bruto), format_currency(v_amort), format_currency(v_retencoes), format_currency(v_liquido)],
            y=[v_bruto, v_amort, v_retencoes, v_liquido],
            connector={"line": {"color": COLORS['neutral']}},
            decreasing={"marker": {"color": "#ef553b"}},
            increasing={"marker": {"color": "#00cc96"}},
            totals={"marker": {"color": COLORS['primary']}}
        ))
        fig.update_layout(height=350, margin=dict(t=20, b=20, l=10, r=10))
        st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

with col_s:
    st.markdown("#### Resumo por Status/Cliente")
    if not df_receber.empty:
        df_status = df_receber.groupby('status_titulo')['valor_bruto'].agg(['sum', 'count']).reset_index()
        df_status.columns = ['Status', 'Valor', 'Qtd']
        st.dataframe(
            df_status,
            column_config={"Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f")},
            width='stretch', height=180, hide_index=True
        )

        st.write("") # Espaçador pequeno
        df_cli = df_receber.groupby('cliente')['valor_bruto'].sum().sort_values(ascending=False).reset_index()
        df_cli.columns = ['Cliente', 'Valor Total']
        st.dataframe(
            df_cli,
            column_config={"Valor Total": st.column_config.NumberColumn("Total", format="R$ %.2f")},
            width='stretch', height=180, hide_index=True
        )

st.markdown("---")

# --- LINHA 2: TABELA DETALHADA ---
st.markdown("#### Detalhamento por Nota Fiscal")

if not df_receber.empty:
    status_opts = ["Todos Status"] + sorted(df_receber['status_titulo'].dropna().unique().tolist())
    status_sel  = st.selectbox("Status", status_opts, key="f_st_receb", label_visibility="collapsed")
    df_show = df_receber if status_sel == "Todos Status" else df_receber[df_receber['status_titulo'] == status_sel]

    st.dataframe(
        df_show[['nf', 'cliente', 'valor_bruto', 'impostos', 'valor_liquido', 'data_vencimento', 'status_titulo']],
        column_config={
            "valor_bruto":   st.column_config.NumberColumn("Bruto",   format="R$ %.2f"),
            "impostos":      st.column_config.NumberColumn("Imp.",    format="R$ %.2f"),
            "valor_liquido": st.column_config.NumberColumn("Líquido", format="R$ %.2f"),
        },
        width='stretch',
        hide_index=True,
        height=350
    )
