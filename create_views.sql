-- ---------------------------------------------------------
-- SCRIPTS SQL PARA MODELAGEM DE BI (POSTGRESQL)
-- ---------------------------------------------------------

-- 1. View de Vendas Detalhada (Achatando o JSON 'det')
-- Esta view cria uma linha para cada produto vendido, facilitando o Power BI.
CREATE OR REPLACE VIEW v_omie_vendas_itens AS
SELECT 
    p."cabecalho.codigo_pedido" as pedido_id,
    p."cabecalho.numero_pedido" as pedido_numero,
    p."cabecalho.data_previsao" as data_venda,
    p."cabecalho.codigo_cliente" as codigo_cliente_omie,
    c.razao_social as cliente_nome,
    c.cidade as cliente_cidade,
    c.estado as cliente_uf,
    -- Extraindo dados do item (JSON)
    (det_item.value->'ide'->>'codigo_item')::bigint as produto_id,
    (det_item.value->'inf_adic'->>'peso_bruto')::float as peso,
    (det_item.value->'prod'->>'descricao') as produto_nome,
    (det_item.value->'prod'->>'quantidade')::float as quantidade,
    (det_item.value->'prod'->>'valor_unitario')::float as valor_unitario,
    ((det_item.value->'prod'->>'quantidade')::float * (det_item.value->'prod'->>'valor_unitario')::float) as valor_total_item
FROM 
    omie_pedidos_venda p
LEFT JOIN 
    omie_clientes c ON p."cabecalho.codigo_cliente" = c.codigo_cliente_omie
CROSS JOIN LATERAL 
    jsonb_array_elements(p.det::jsonb) AS det_item;


-- 2. View de Resumo Financeiro (Se os lanamentos funcionarem)
-- Agrupando por categoria financeira
CREATE OR REPLACE VIEW v_omie_financeiro_resumo AS
SELECT 
    codigo_categoria,
    data_vencimento,
    valor_lancamento,
    status_lancamento,
    CASE WHEN valor_lancamento > 0 THEN 'Receita' ELSE 'Despesa' END as tipo
FROM 
    omie_lancamentos_financeiros;
