-- Query 8: Repeat Purchase Rate & Customer Frequency Metrics
-- Evaluates the percentage of customers with > 1 completed order.

WITH customer_order_counts AS (
    SELECT
        customer_id,
        COUNT(DISTINCT order_id) AS order_count
    FROM orders
    WHERE status IN ('Delivered', 'Shipped')
    GROUP BY customer_id
)
SELECT
    COUNT(*) AS total_customers_with_orders,
    SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) AS repeat_customers,
    ROUND(
        100.0 * SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) / COUNT(*), 2
    ) AS repeat_purchase_rate_pct,
    ROUND(AVG(order_count), 2) AS avg_orders_per_customer,
    MAX(order_count) AS max_orders_single_customer
FROM customer_order_counts;
