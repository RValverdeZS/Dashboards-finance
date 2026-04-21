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

# --- KPIs de Recebimento (Reorganizados conforme solicitação) ---
if kpi is not None:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    # 1. Total Faturado
    c1.metric("Total Faturado", format_currency(kpi['valor_faturado']))
    
    # 2. % Faturado
    v_contrato = kpi['valor_contrato'] if kpi['valor_contrato'] > 0 else 1
    pct_faturado = (kpi['valor_faturado'] / v_contrato * 100)
    c2.metric("% Faturado",     f"{pct_faturado:.1f}%")
    
    # 3. Amortizado
    c3.metric("Amortizado",     format_currency(kpi['total_amortizado']))
    
    # 4. Adiantado
    c4.metric("Adiantado",      format_currency(kpi['total_adiantado']))
    
    # 5. Performance
    c5.metric("Performance",    format_currency(kpi['total_retencao_performance']))
    
    # 6. Seguro
    c6.metric("Seguro",         format_currency(kpi['total_retencao_seguro']))

st.markdown("---")

# --- LINHA 1: WATERFALL ---
st.markdown("#### Composição dos Recebimentos")
if kpi is not None:
    v_bruto     = kpi['valor_faturado']
    v_amort     = -kpi['total_amortizado']
    v_retencoes = -(kpi['total_retencao_performance'] + kpi['total_retencao_seguro'])
    v_liquido   = v_bruto + v_amort + v_retencoes

    fig = go.Figure(go.Waterfall(
        name="Fluxo", orientation="v",
        measure=["absolute", "relative", "relative", "total"],
        x=["Bruto", "Amortização", "Retenções", "Líquido"],
        textposition="outside",
        text=[format_currency(v_bruto), format_currency(v_amort), format_currency(v_retencoes), format_currency(v_liquido)],
        y=[v_bruto, v_amort, v_retencoes, v_liquido],
        connector={"line": {"color": COLORS['neutral']}},
        decreasing={"marker": {"color": "#ef553b"}},
        increasing={"marker": {"color": "#00cc96"}},
        totals={"marker": {"color": COLORS['primary']}}
    ))
    fig.update_layout(height=400, margin=dict(t=30, b=30, l=10, r=10), showlegend=False)
    st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

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
        height=400
    )
