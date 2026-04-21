-- 5. Programação de Resgates (Semanal - Segundas-feiras)
DROP VIEW IF EXISTS v_dashboard_programacao_resgates CASCADE;
CREATE VIEW v_dashboard_programacao_resgates AS
WITH segundas AS (
    -- Gera as segundas-feiras do mês atual (Abril 2026)
    SELECT 
        d::date as data_segunda,
        'Semana ' || row_number() OVER (ORDER BY d) as semana_label
    FROM generate_series(
        '2026-04-01'::date, 
        '2026-04-30'::date, 
        '1 day'::interval
    ) d
    WHERE extract(dow from d) = 1 -- 1 = Segunda-feira
),
pagamentos_semanais AS (
    SELECT 
        s.semana_label,
        s.data_segunda,
        COALESCE(SUM(p.valor_documento), 0) as total_pagar
    FROM segundas s
    LEFT JOIN omie_contas_pagar p ON 
        p.data_vencimento::DATE >= s.data_segunda 
        AND p.data_vencimento::DATE < (s.data_segunda + interval '7 days')
        AND p.status_titulo = 'A VENCER'
    GROUP BY s.semana_label, s.data_segunda
),
saldo_anterior AS (
    -- Saldo inicial fixo do fechamento de Março de 2026
    SELECT 16565862.36 as saldo_inicial
)
SELECT 
    ps.semana_label,
    ps.data_segunda,
    ps.total_pagar,
    -- Saldo estimado (Saldo Inicial - Soma acumulada dos pagamentos até aqui)
    (sa.saldo_inicial - SUM(ps.total_pagar) OVER (ORDER BY ps.data_segunda)) as saldo_estimado,
    -- Valor a Resgatar (Se o saldo estimado for negativo, precisamos resgate)
    CASE 
        WHEN (sa.saldo_inicial - SUM(ps.total_pagar) OVER (ORDER BY ps.data_segunda)) < 0 
        THEN ABS(sa.saldo_inicial - SUM(ps.total_pagar) OVER (ORDER BY ps.data_segunda))
        ELSE 0 
    END as necessidade_resgate
FROM pagamentos_semanais ps, saldo_anterior sa;
