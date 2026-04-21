-- View Especial para o Gráfico de Cascata (Bridge) da Página 3
DROP VIEW IF EXISTS v_dashboard_recebimentos_ponte CASCADE;
CREATE VIEW v_dashboard_recebimentos_ponte AS
SELECT 
    numero_documento as "NF",
    ordem,
    "Categoria",
    "Valor"
FROM (
    SELECT 
        numero_documento,
        1 as ordem, '1. Valor Bruto' as "Categoria", valor_documento as "Valor"
    FROM omie_contas_receber
    WHERE valor_documento > 0
    
    UNION ALL
    
    SELECT 
        cr.numero_documento,
        2 as ordem, '2. Impostos (ISS/INSS/IR)' as "Categoria", -(COALESCE(cr.valor_iss,0) + COALESCE(cr.valor_inss,0) + COALESCE(cr.valor_ir,0)) as "Valor"
    FROM omie_contas_receber cr
    WHERE valor_documento > 0
    
    UNION ALL
    
    SELECT 
        cr.numero_documento,
        3 as ordem, '3. Amortizacao' as "Categoria", -COALESCE(k.total_amortizado,0) as "Valor"
    FROM omie_contas_receber cr
    LEFT JOIN v_dashboard_contrato_item_detalhado k ON cr.codigo_lancamento_omie = k.codigo_lancamento_omie
    WHERE valor_documento > 0
    
    UNION ALL
    
    SELECT 
        cr.numero_documento,
        4 as ordem, '4. Retencoes (Perf/Seg)' as "Categoria", -(COALESCE(k.total_retencao_performance,0) + COALESCE(k.total_retencao_seguro,0)) as "Valor"
    FROM omie_contas_receber cr
    LEFT JOIN v_dashboard_contrato_item_detalhado k ON cr.codigo_lancamento_omie = k.codigo_lancamento_omie
    WHERE valor_documento > 0
) t
ORDER BY ordem;
