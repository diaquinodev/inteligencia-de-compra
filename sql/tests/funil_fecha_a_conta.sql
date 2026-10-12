-- Nenhuma linha some sem explicação entre a origem e a análise:
-- origem = repetidas + excluídas (com motivo) + válidas,
-- e válidas = preço suspeito + grupo pequeno + comparáveis (em linhas e em valor).
WITH etapas AS (
    SELECT
        SUM(IF(q.ordem = 1, q.linhas, 0)) AS origem,
        SUM(IF(q.ordem = 2, q.linhas, 0)) AS repetidas,
        SUM(IF(q.ordem = 3, q.linhas, 0)) AS excluidas,
        SUM(IF(q.ordem = 4, q.linhas, 0)) AS validas,
        SUM(IF(q.ordem IN (5, 6, 7), q.linhas, 0)) AS validas_por_destino,
        ROUND(SUM(IF(q.ordem = 4, q.valor, 0)), 2) AS valor_validas,
        ROUND(SUM(IF(q.ordem IN (5, 6, 7), q.valor, 0)), 2) AS valor_por_destino
    FROM qualidade_resumo AS q
)

SELECT
    e.origem,
    e.repetidas,
    e.excluidas,
    e.validas,
    e.validas_por_destino,
    e.valor_validas,
    e.valor_por_destino,
    e.origem - (e.repetidas + e.excluidas + e.validas) AS linhas_sem_explicacao
FROM etapas AS e
WHERE
    e.origem != e.repetidas + e.excluidas + e.validas
    OR e.validas != e.validas_por_destino
    OR e.valor_validas != e.valor_por_destino;
