-- RevenueLens — SQL Analysis Queries
-- Covers the main business questions I wanted to answer with this dataset.
-- All revenue = quantity * unit_price * (1 - discount)
-- Only counting Delivered + Shipped orders (excluding Cancelled/Returned)


-- 1. Monthly Revenue Trend + Month-over-Month Growth
--    Wanted to see if there's a clear seasonal pattern and how consistent growth is.

WITH monthly AS (
    SELECT
        strftime('%Y-%m', o.order_date) AS year_month,
        ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status IN ('Delivered', 'Shipped')
    GROUP BY 1
    ORDER BY 1
)
SELECT
    year_month,
    revenue,
    LAG(revenue) OVER (ORDER BY year_month) AS prev_month_revenue,
    ROUND(
        100.0 * (revenue - LAG(revenue) OVER (ORDER BY year_month))
              / LAG(revenue) OVER (ORDER BY year_month), 2
    ) AS mom_growth_pct
FROM monthly;


-- 2. Top 10 Products by Revenue
--    Which SKUs are driving the most money?

SELECT
    p.product_id,
    p.name AS product_name,
    p.category,
    p.sub_category,
    COUNT(DISTINCT oi.order_id) AS orders_count,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2) AS total_revenue
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
JOIN orders   o ON o.order_id   = oi.order_id
WHERE o.status IN ('Delivered', 'Shipped')
GROUP BY p.product_id, p.name, p.category, p.sub_category
ORDER BY total_revenue DESC
LIMIT 10;


-- 3. Top 10 Products by Profit Margin
--    High revenue != high profit. Wanted to separate these two.

SELECT
    p.product_id,
    p.name AS product_name,
    p.category,
    p.price,
    p.cost,
    ROUND(p.price - p.cost, 2) AS gross_margin_per_unit,
    ROUND(100.0 * (p.price - p.cost) / p.price, 2) AS margin_pct,
    ROUND(SUM(oi.quantity * (oi.unit_price - p.cost) * (1 - oi.discount)), 2) AS total_profit
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
JOIN orders   o ON o.order_id   = oi.order_id
WHERE o.status IN ('Delivered', 'Shipped')
GROUP BY p.product_id, p.name, p.category, p.price, p.cost
ORDER BY margin_pct DESC
LIMIT 10;


-- 4a. Revenue by Region
--     Checking if the regional split roughly matches the customer distribution.

SELECT
    c.region,
    COUNT(DISTINCT c.customer_id) AS total_customers,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2) AS total_revenue,
    ROUND(AVG(oi.quantity * oi.unit_price * (1 - oi.discount)), 2) AS avg_item_revenue
FROM customers c
JOIN orders      o  ON o.customer_id = c.customer_id
JOIN order_items oi ON oi.order_id   = o.order_id
WHERE o.status IN ('Delivered', 'Shipped')
GROUP BY c.region
ORDER BY total_revenue DESC;


-- 4b. Revenue by Category
--     Which category is carrying the most weight?

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


-- 5. RFM Segmentation
--    Segments customers by Recency, Frequency, Monetary using NTILE quartiles.
--    Labels like Champions, At Risk etc. based on combined score.

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


-- 6. Cohort Retention Analysis
--    Groups customers by their signup month and tracks how many stay active
--    in each subsequent month. Classic retention funnel view.

WITH cohort_base AS (
    SELECT
        c.customer_id,
        strftime('%Y-%m', c.signup_date) AS cohort_month,
        strftime('%Y-%m', o.order_date)  AS order_month
    FROM customers c
    JOIN orders o ON o.customer_id = c.customer_id
    WHERE o.status IN ('Delivered', 'Shipped')
),
cohort_periods AS (
    SELECT
        cohort_month,
        order_month,
        CAST(
            (strftime('%Y', order_month) - strftime('%Y', cohort_month)) * 12
          + (strftime('%m', order_month) - strftime('%m', cohort_month))
        AS INTEGER) AS period_number,
        COUNT(DISTINCT customer_id) AS active_customers
    FROM cohort_base
    GROUP BY cohort_month, order_month
),
cohort_sizes AS (
    SELECT cohort_month, active_customers AS cohort_size
    FROM cohort_periods
    WHERE period_number = 0
)
SELECT
    cp.cohort_month,
    cs.cohort_size,
    cp.period_number,
    cp.active_customers,
    ROUND(100.0 * cp.active_customers / cs.cohort_size, 1) AS retention_pct
FROM cohort_periods cp
JOIN cohort_sizes cs ON cs.cohort_month = cp.cohort_month
WHERE cp.period_number BETWEEN 0 AND 11
ORDER BY cp.cohort_month, cp.period_number;


-- 7. Repeat Purchase Rate
--    Simple but important — what % of customers bought more than once?

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
