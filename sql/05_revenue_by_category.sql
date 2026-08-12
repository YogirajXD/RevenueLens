-- Query 5: Revenue Share by Product Category
-- Calculates gross revenue and overall percentage revenue share per vertical.

SELECT
    p.category,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2) AS total_revenue,
    ROUND(100.0 * SUM(oi.quantity * oi.unit_price * (1 - oi.discount))
        / SUM(SUM(oi.quantity * oi.unit_price * (1 - oi.discount))) OVER (), 2) AS revenue_share_pct
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
JOIN orders   o ON o.order_id   = oi.order_id
WHERE o.status IN ('Delivered', 'Shipped')
GROUP BY p.category
ORDER BY total_revenue DESC;
