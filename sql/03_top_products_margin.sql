-- Query 3: Top 10 Products by Profit Margin Percentage
-- Evaluates product unit economics by calculating gross profit margin %.

SELECT
    p.product_id,
    p.name AS product_name,
    p.category,
    p.price,
    p.cost,
    ROUND(p.price - p.cost, 2) AS gross_margin_per_unit,
    ROUND(100.0 * (p.price - p.cost) / p.price, 2) AS margin_pct,
    ROUND(SUM(oi.quantity * (oi.unit_price - p.cost) * (1 - oi.discount)), 2) AS total_gross_profit
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
JOIN orders   o ON o.order_id   = oi.order_id
WHERE o.status IN ('Delivered', 'Shipped')
GROUP BY p.product_id, p.name, p.category, p.price, p.cost
ORDER BY margin_pct DESC
LIMIT 10;
