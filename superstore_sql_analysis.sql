-- ============================================================
-- SUPERSTORE SALES & REVENUE ANALYSIS
-- Tools: SQL (MySQL compatible) | Dataset: 9,994 orders
-- Author: Aman Kumar Choudhary
-- ============================================================

-- SETUP: Create and load table
CREATE TABLE IF NOT EXISTS superstore (
    row_id       INT,
    order_id     VARCHAR(20),
    order_date   DATE,
    ship_date    DATE,
    ship_mode    VARCHAR(30),
    customer_id  VARCHAR(10),
    customer_name VARCHAR(50),
    segment      VARCHAR(20),
    country      VARCHAR(30),
    state        VARCHAR(30),
    region       VARCHAR(20),
    category     VARCHAR(30),
    sub_category VARCHAR(30),
    sales        DECIMAL(12,2),
    quantity     INT,
    discount     DECIMAL(5,2),
    profit       DECIMAL(12,2)
);

-- LOAD DATA (update path as needed)
-- LOAD DATA INFILE '/path/to/superstore_sales.csv'
-- INTO TABLE superstore FIELDS TERMINATED BY ',' IGNORE 1 ROWS;

-- ============================================================
-- QUERY 1: Monthly Revenue Trend
-- ============================================================
SELECT
    DATE_FORMAT(order_date, '%Y-%m')   AS month,
    COUNT(DISTINCT order_id)           AS total_orders,
    ROUND(SUM(sales), 2)               AS total_revenue,
    ROUND(SUM(profit), 2)              AS total_profit,
    ROUND(AVG(sales), 2)               AS avg_order_value,
    ROUND(SUM(profit)/SUM(sales)*100, 2) AS profit_margin_pct
FROM superstore
GROUP BY month
ORDER BY month;


-- ============================================================
-- QUERY 2: Top 10 Customers by Revenue (with JOIN pattern)
-- ============================================================
SELECT
    s.customer_name,
    s.segment,
    COUNT(DISTINCT s.order_id)           AS total_orders,
    ROUND(SUM(s.sales), 2)               AS total_revenue,
    ROUND(SUM(s.profit), 2)              AS total_profit,
    ROUND(SUM(s.profit)/SUM(s.sales)*100, 2) AS profit_margin_pct,
    ROUND(AVG(s.discount)*100, 1)        AS avg_discount_pct
FROM superstore s
JOIN (
    SELECT customer_name, SUM(sales) AS rev
    FROM superstore
    GROUP BY customer_name
    ORDER BY rev DESC
    LIMIT 10
) top10 ON s.customer_name = top10.customer_name
GROUP BY s.customer_name, s.segment
ORDER BY total_revenue DESC;


-- ============================================================
-- QUERY 3: Category-wise Performance with Margin Tier (CASE)
-- ============================================================
SELECT
    category,
    COUNT(DISTINCT order_id)              AS total_orders,
    ROUND(SUM(sales), 2)                  AS total_revenue,
    ROUND(SUM(profit), 2)                 AS total_profit,
    ROUND(AVG(discount)*100, 1)           AS avg_discount_pct,
    ROUND(SUM(profit)/SUM(sales)*100, 2)  AS profit_margin_pct,
    CASE
        WHEN SUM(profit)/SUM(sales)*100 >= 15 THEN 'High Margin'
        WHEN SUM(profit)/SUM(sales)*100 >= 8  THEN 'Medium Margin'
        ELSE 'Low Margin'
    END AS margin_tier
FROM superstore
GROUP BY category
ORDER BY total_revenue DESC;


-- ============================================================
-- QUERY 4: Sub-category Profitability Breakdown
-- ============================================================
SELECT
    category,
    sub_category,
    ROUND(SUM(sales), 2)                  AS revenue,
    ROUND(SUM(profit), 2)                 AS profit,
    ROUND(SUM(profit)/SUM(sales)*100, 2)  AS profit_margin_pct,
    COUNT(DISTINCT order_id)              AS orders,
    CASE
        WHEN SUM(profit) < 0                   THEN 'Loss-Making'
        WHEN SUM(profit)/SUM(sales)*100 < 8    THEN 'Low Margin'
        WHEN SUM(profit)/SUM(sales)*100 < 18   THEN 'Medium Margin'
        ELSE 'High Margin'
    END AS performance_tag
FROM superstore
GROUP BY category, sub_category
ORDER BY profit_margin_pct DESC;


-- ============================================================
-- QUERY 5: Regional Performance — Identify Underperformers
-- ============================================================
SELECT
    region,
    COUNT(DISTINCT order_id)              AS total_orders,
    ROUND(SUM(sales), 2)                  AS total_revenue,
    ROUND(SUM(profit), 2)                 AS total_profit,
    ROUND(AVG(discount)*100, 1)           AS avg_discount_pct,
    ROUND(SUM(profit)/SUM(sales)*100, 2)  AS profit_margin_pct,
    CASE
        WHEN SUM(sales) < (
            SELECT AVG(reg_sales)
            FROM (SELECT region, SUM(sales) AS reg_sales FROM superstore GROUP BY region) r
        ) THEN 'Underperforming'
        ELSE 'On Target'
    END AS performance_status
FROM superstore
GROUP BY region
ORDER BY total_revenue DESC;


-- ============================================================
-- QUERY 6: Discount vs Profit Relationship (Core Insight)
-- ============================================================
SELECT
    CASE
        WHEN discount = 0       THEN '1. No Discount'
        WHEN discount <= 0.10   THEN '2. Low (1-10%)'
        WHEN discount <= 0.20   THEN '3. Medium (11-20%)'
        WHEN discount <= 0.30   THEN '4. High (21-30%)'
        ELSE                         '5. Very High (31%+)'
    END AS discount_tier,
    COUNT(order_id)                        AS total_orders,
    ROUND(AVG(sales), 2)                   AS avg_sales,
    ROUND(AVG(profit), 2)                  AS avg_profit,
    ROUND(SUM(profit), 2)                  AS total_profit,
    SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) AS loss_orders,
    ROUND(SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) / COUNT(*) * 100, 1) AS loss_rate_pct
FROM superstore
GROUP BY discount_tier
ORDER BY discount_tier;


-- ============================================================
-- QUERY 7: Region × Category Cross Analysis (JOIN)
-- ============================================================
SELECT
    s.region,
    s.category,
    ROUND(SUM(s.sales), 2)                AS revenue,
    ROUND(SUM(s.profit), 2)               AS profit,
    ROUND(SUM(s.profit)/SUM(s.sales)*100, 2) AS margin_pct,
    ROUND(AVG(s.discount)*100, 1)         AS avg_discount_pct
FROM superstore s
JOIN (
    SELECT region, SUM(sales) AS region_total
    FROM superstore
    GROUP BY region
) rt ON s.region = rt.region
GROUP BY s.region, s.category
ORDER BY s.region, revenue DESC;


-- ============================================================
-- QUERY 8: Year-over-Year Revenue Growth
-- ============================================================
SELECT
    YEAR(order_date) AS year,
    ROUND(SUM(sales), 2)     AS total_revenue,
    ROUND(SUM(profit), 2)    AS total_profit,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(
        (SUM(sales) - LAG(SUM(sales)) OVER (ORDER BY YEAR(order_date)))
        / LAG(SUM(sales)) OVER (ORDER BY YEAR(order_date)) * 100, 1
    ) AS yoy_growth_pct
FROM superstore
GROUP BY YEAR(order_date)
ORDER BY year;

