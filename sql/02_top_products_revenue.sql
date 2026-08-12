-- Query 2: Top 10 Products by Total Revenue
-- Identifies top performing SKUs based on total gross revenue generated.

SELECT
    p.product_id,
    p.name AS product_name,
    p.category,
    p.sub_category,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    SUM(oi.quantity) AS total_units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2) AS total_revenue
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
JOIN orders   o ON o.order_id   = oi.order_id
WHERE o.status IN ('Delivered', 'Shipped')
GROUP BY p.product_id, p.name, p.category, p.sub_category
ORDER BY total_revenue DESC
LIMIT 10;
