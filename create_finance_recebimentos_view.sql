-- 6. Página 3 - Recebimentos Detalhados (Foco na Planilha 7B_Recebimentos Realizados)
DROP VIEW IF EXISTS v_dashboard_recebimentos_detalhes CASCADE;
CREATE VIEW v_dashboard_recebimentos_detalhes AS
WITH kpi_p2 AS (
    -- Reutilizamos a lógica de extração da Página 2 para bater os valores
    SELECT 
        codigo_lancamento_omie,
        total_amortizado,
        total_retencao_performance,
        total_retencao_seguro
    FROM public.v_dashboard_contrato_item_detalhado
)
SELECT 
    cr.data_emissao as "Data Emissao",
    cr.data_vencimento as "Data Vencimento",
    cr.status_titulo as "Status",
    -- NF: Formata como "Medição X" usando o sequencial do contrato
    CASE
        WHEN cr.numero_documento_fiscal IS NOT NULL AND cr.numero_documento_fiscal != ''
            THEN 'Medição ' || cr.numero_documento_fiscal
        WHEN cr.numero_documento IS NOT NULL AND cr.numero_documento != ''
            THEN 'Doc. ' || cr.numero_documento
        ELSE 'Lançamento Avulso'
    END as "NF",
    cr.valor_documento as "Valor Bruto",
    -- Impostos
    COALESCE(cr.valor_iss, 0) as "ISS Retido",
    COALESCE(cr.valor_inss, 0) as "INSS Retido",
    COALESCE(cr.valor_ir, 0) as "IRRF Retido",
    -- Deduções Contratuais (Vindas da lógica da P2)
    COALESCE(k2.total_amortizado, 0) as "Amortizacao",
    COALESCE(k2.total_retencao_performance, 0) as "Retencao Performance",
    COALESCE(k2.total_retencao_seguro, 0) as "Retencao Seguro",
    -- Valor Líquido Real (O que sobra após impostos e retenções)
    (cr.valor_documento 
        - COALESCE(cr.valor_iss, 0) 
        - COALESCE(cr.valor_inss, 0) 
        - COALESCE(cr.valor_ir, 0)
        - COALESCE(k2.total_amortizado, 0)
        - COALESCE(k2.total_retencao_performance, 0)
        - COALESCE(k2.total_retencao_seguro, 0)
    ) as "Valor Liquido Real"
FROM omie_contas_receber cr
LEFT JOIN kpi_p2 k2 ON cr.codigo_lancamento_omie = k2.codigo_lancamento_omie
WHERE cr.valor_documento > 0
ORDER BY cr.data_emissao DESC;

-- View de KPIs para os Cartões da Página 3
DROP VIEW IF EXISTS v_dashboard_kpis_recebimentos CASCADE;
CREATE VIEW v_dashboard_kpis_recebimentos AS
SELECT 
    SUM("Valor Bruto") as total_faturado,
    SUM("ISS Retido" + "INSS Retido" + "IRRF Retido") as total_impostos_retidos,
    SUM("Amortizacao" + "Retencao Performance" + "Retencao Seguro") as total_deducoes_contratuais,
    SUM("Valor Liquido Real") as total_recebido_liquido,
    -- Eficiência de Caixa (Líquido / Bruto)
    CASE 
        WHEN SUM("Valor Bruto") > 0 
        THEN (SUM("Valor Liquido Real") / SUM("Valor Bruto")) * 100 
        ELSE 0 
    END as eficiencia_caixa_perc
FROM v_dashboard_recebimentos_detalhes;
