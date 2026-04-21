-- Views para o Dashboard Financeiro Omie - Consórcio 7B (UNIFICADA)

-- 1. Pagamentos Realizados (Unificado: Omie + Planilhas de Apoio)
DROP VIEW IF EXISTS v_dashboard_pagamentos_realizados CASCADE;
CREATE VIEW v_dashboard_pagamentos_realizados AS
WITH unified_pgtos AS (
    -- Dados Oficiais do Omie
    SELECT 
        l."cabecalho.dDtLanc"::DATE as data_evento,
        l."cabecalho.nValorLanc"::numeric as valor,
        CASE 
            WHEN l."detalhes.nCodCliente" = 0 THEN 'Transferência / Transf. entre Contas'
            WHEN f.nome_fantasia IS NOT NULL AND f.nome_fantasia != '' THEN f.nome_fantasia
            WHEN f.razao_social IS NOT NULL AND f.razao_social != '' THEN f.razao_social
            WHEN cat.descricao IS NOT NULL AND cat.descricao != '' THEN 'Gasto s/ Nome (' || cat.descricao || ')'
            ELSE 'Fornecedor sem Nome (' || l."detalhes.nCodCliente" || ')'
        END as fornecedor,
        COALESCE(cat.descricao, 'Categoria ID: ' || l."detalhes.cCodCateg", 'Lançamento Sem Categoria') as categoria,
        l."detalhes.cNumDoc"::text as nf,
        l."detalhes.cObs" as observacoes,
        'OMIE' as origem
    FROM 
        omie_lancamentos_financeiros l
    LEFT JOIN omie_clientes f ON l."detalhes.nCodCliente" = f.codigo_cliente_omie
    LEFT JOIN omie_categorias cat ON l."detalhes.cCodCateg" = cat.codigo
    WHERE l."diversos.cNatureza" = 'P'

    UNION ALL

    -- Dados Manuais das Planilhas de Apoio
    SELECT 
        data_evento::DATE,
        valor::numeric,
        fornecedor,
        categoria,
        nf::text,
        'Planilha de Apoio' as observacoes,
        'MANUAL' as origem
    FROM manual_pagamentos_realizados
)
SELECT 
    data_evento,
    valor,
    fornecedor,
    categoria,
    nf,
    observacoes,
    origem,
    CASE 
        WHEN fornecedor ILIKE '%LFM%' OR observacoes ILIKE '%LFM%' THEN 'LFM'
        WHEN fornecedor ILIKE '%ENOTEC%' OR observacoes ILIKE '%ENOTEC%' THEN 'ENOTEC'
        WHEN fornecedor ILIKE '%COBRAPE%' OR observacoes ILIKE '%COBRAPE%' THEN 'COBRAPE'
        ELSE 'Operacional'
    END as socio,
    '7B' as projeto
FROM unified_pgtos;

-- 2. Pagamentos Projetados (Unificado: Omie + Planilhas de Apoio)
DROP VIEW IF EXISTS v_dashboard_pagamentos_projetados CASCADE;
CREATE VIEW v_dashboard_pagamentos_projetados AS
WITH unified_previsao AS (
    -- Dados do Omie (Títulos em aberto)
    SELECT 
        l.data_vencimento::DATE as data_evento,
        l.valor_documento::numeric as valor,
        COALESCE(f.razao_social, f.nome_fantasia, l.codigo_categoria) as fornecedor,
        cat.descricao as categoria,
        l.numero_documento_fiscal::text as nf,
        l.distribuicao as observacoes,
        l."info.dInc" as data_registro,
        l."info.hInc" as hora_registro,
        'OMIE' as origem
    FROM 
        omie_contas_pagar l
    LEFT JOIN omie_clientes f ON l.codigo_cliente_fornecedor = f.codigo_cliente_omie
    LEFT JOIN omie_categorias cat ON l.codigo_categoria = cat.codigo
    WHERE l.status_titulo = 'A VENCER'

    UNION ALL

    -- Dados Manuais das Planilhas de Apoio (Planejamento)
    SELECT 
        data_vencimento::DATE as data_evento,
        valor::numeric as valor,
        fornecedor,
        categoria,
        nf::text,
        'Projeção Planilha' as observacoes,
        data_vencimento::text as data_registro, -- Fallback para ordenação
        '00:00:00' as hora_registro,
        'MANUAL' as origem
    FROM manual_contas_pagar
)
SELECT 
    data_evento,
    valor,
    fornecedor,
    categoria,
    nf,
    observacoes,
    data_registro,
    hora_registro,
    origem,
    '7B' as projeto,
    TO_CHAR(data_evento::DATE, 'TMMonth/YYYY') as mes_ano,
    EXTRACT(MONTH FROM data_evento::DATE) as mes_num,
    EXTRACT(YEAR FROM data_evento::DATE) as ano,
    CEIL(EXTRACT(DAY FROM data_evento::DATE) / 7.0)::INT || 'a Semana' as semana_do_mes,
    CASE EXTRACT(DOW FROM data_evento::DATE)
        WHEN 0 THEN '7-Domingo'
        WHEN 1 THEN '1-Segunda-feira'
        WHEN 2 THEN '2-Terca-feira'
        WHEN 3 THEN '3-Quarta-feira'
        WHEN 4 THEN '4-Quinta-feira'
        WHEN 5 THEN '5-Sexta-feira'
        WHEN 6 THEN '6-Sabado'
    END as dia_semana
FROM unified_previsao;

-- 3. KPIs Totais do Contrato
DROP VIEW IF EXISTS v_dashboard_kpis_contrato CASCADE;
CREATE VIEW v_dashboard_kpis_contrato AS
WITH base_kpis AS (
    SELECT 
        (SELECT valor_total_contrato FROM manual_contrato_7b LIMIT 1) as valor_contrato,
        (SELECT SUM(valor_documento) FROM omie_contas_receber) as valor_faturado,
        (SELECT SUM(valor) FROM v_dashboard_pagamentos_realizados) as custo_pago,
        (SELECT SUM(valor) FROM v_dashboard_pagamentos_realizados WHERE categoria ILIKE '%Adiantamento%') as total_adiantado,
        (SELECT SUM(valor) FROM v_dashboard_pagamentos_projetados) as custo_total_previsto,
        (SELECT SUM(valor_documento) FROM omie_contas_receber WHERE status_titulo = 'RECEBIDO') as total_recebido,
        -- Campos de Amortização e Retenção para WaterFall (Vindos da Omie Contas Receber se disponíveis ou 0 por enquanto)
        (SELECT COALESCE(SUM(valor_documento * 0.1), 0) FROM omie_contas_receber) as total_amortizado, -- Exemplo de cálculo se não houver campo direto
        (SELECT COALESCE(SUM(valor_documento * 0.05), 0) FROM omie_contas_receber) as total_retencao_performance,
        (SELECT COALESCE(SUM(valor_documento * 0.02), 0) FROM omie_contas_receber) as total_retencao_seguro
)
SELECT 
    *,
    CASE WHEN custo_total_previsto > 0 THEN (custo_pago / custo_total_previsto) ELSE 0 END as pct_custo_pago
FROM base_kpis;
