-- Query 7: Customer Cohort Retention Analysis by Signup Month
-- Tracks monthly active customer retention percentages across signup cohorts (periods 0-11).

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
