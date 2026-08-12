-- Query 6: RFM Customer Segmentation (Recency, Frequency, Monetary)
-- Scores each customer into quartiles (1-4) across Recency, Frequency, and Monetary value
-- using the NTILE() window function, and assigns RFM Segment labels.

WITH rfm_raw AS (
    SELECT
        c.customer_id,
        c.name,
        c.region,
        c.segment,
        CAST(julianday('2026-01-01') - julianday(MAX(o.order_date)) AS INTEGER) AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2) AS monetary
    FROM customers c
    JOIN orders      o  ON o.customer_id = c.customer_id
    JOIN order_items oi ON oi.order_id   = o.order_id
    WHERE o.status IN ('Delivered', 'Shipped')
    GROUP BY c.customer_id, c.name, c.region, c.segment
),
rfm_scored AS (
    SELECT *,
        NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(4) OVER (ORDER BY frequency   ASC)  AS f_score,
        NTILE(4) OVER (ORDER BY monetary    ASC)  AS m_score
    FROM rfm_raw
),
rfm_segmented AS (
    SELECT *,
        (r_score + f_score + m_score) AS rfm_total,
        CASE
            WHEN r_score = 4 AND f_score >= 3 AND m_score >= 3 THEN 'Champions'
            WHEN r_score >= 3 AND f_score >= 3                  THEN 'Loyal'
            WHEN r_score = 4                                     THEN 'Recent'
            WHEN r_score >= 2 AND m_score >= 3                   THEN 'Potential Loyalist'
            WHEN r_score <= 2 AND f_score >= 3                   THEN 'At Risk'
            WHEN r_score = 1  AND f_score >= 2                   THEN 'Lost'
            ELSE                                                      'Needs Attention'
        END AS rfm_segment
    FROM rfm_scored
)
SELECT
    customer_id, name, region, segment,
    recency_days, frequency, monetary,
    r_score, f_score, m_score, rfm_total, rfm_segment
FROM rfm_segmented
ORDER BY rfm_total DESC;
