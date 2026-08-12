-- Query 1: Monthly Revenue Trend & Month-over-Month Growth Percentage
-- Calculates aggregate revenue per month and uses the LAG() window function
-- to compute Month-over-Month (MoM) growth percentage.

WITH monthly_summary AS (
    SELECT
        strftime('%Y-%m', o.order_date) AS year_month,
        ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2) AS monthly_revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status IN ('Delivered', 'Shipped')
    GROUP BY strftime('%Y-%m', o.order_date)
    ORDER BY year_month ASC
)
SELECT
    year_month,
    monthly_revenue,
    LAG(monthly_revenue) OVER (ORDER BY year_month) AS prev_month_revenue,
    ROUND(
        100.0 * (monthly_revenue - LAG(monthly_revenue) OVER (ORDER BY year_month))
              / LAG(monthly_revenue) OVER (ORDER BY year_month), 2
    ) AS mom_growth_pct
FROM monthly_summary;
