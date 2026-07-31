/* ============================================================
   03_advanced_analysis.sql
   Deeper analysis: month-over-month growth, running totals,
   customer ranking within segment, and dormancy risk flagging.
   Demonstrates window functions and CTEs.
   ============================================================ */

-- ------------------------------------------------------------
-- 1. Month-over-month transaction volume growth (%)
-- ------------------------------------------------------------
WITH monthly AS (
    SELECT
        strftime('%Y-%m', transaction_date) AS txn_month,
        COUNT(*)                             AS transaction_count
    FROM transactions
    GROUP BY txn_month
)
SELECT
    txn_month,
    transaction_count,
    LAG(transaction_count) OVER (ORDER BY txn_month)        AS prev_month_count,
    ROUND(
        100.0 * (transaction_count - LAG(transaction_count) OVER (ORDER BY txn_month))
        / NULLIF(LAG(transaction_count) OVER (ORDER BY txn_month), 0)
    , 2)                                                     AS mom_growth_pct
FROM monthly
ORDER BY txn_month;

-- ------------------------------------------------------------
-- 2. Running (cumulative) net cash flow over time
-- ------------------------------------------------------------
WITH monthly_flow AS (
    SELECT
        strftime('%Y-%m', transaction_date) AS txn_month,
        SUM(amount)                          AS net_flow
    FROM transactions
    GROUP BY txn_month
)
SELECT
    txn_month,
    ROUND(net_flow, 2) AS net_flow,
    ROUND(SUM(net_flow) OVER (ORDER BY txn_month), 2) AS cumulative_net_flow
FROM monthly_flow
ORDER BY txn_month;

-- ------------------------------------------------------------
-- 3. Rank customers by balance within their segment
-- (identify high-value customers for relationship management)
-- ------------------------------------------------------------
WITH customer_balances AS (
    SELECT
        c.customer_id,
        c.first_name || ' ' || c.last_name AS customer_name,
        c.segment,
        SUM(a.current_balance)             AS total_balance
    FROM customers c
    JOIN accounts a ON a.customer_id = c.customer_id
    GROUP BY c.customer_id, customer_name, c.segment
)
SELECT
    customer_id,
    customer_name,
    segment,
    total_balance,
    RANK() OVER (PARTITION BY segment ORDER BY total_balance DESC) AS rank_in_segment
FROM customer_balances
ORDER BY segment, rank_in_segment
LIMIT 30;

-- ------------------------------------------------------------
-- 4. Dormancy risk flag: accounts with no transactions
--    in the trailing 90 days of the dataset (re-engagement targets)
-- ------------------------------------------------------------
WITH last_txn AS (
    SELECT
        account_id,
        MAX(transaction_date) AS last_transaction_date
    FROM transactions
    GROUP BY account_id
),
dataset_max_date AS (
    SELECT MAX(transaction_date) AS max_date FROM transactions
)
SELECT
    a.account_id,
    a.account_type,
    a.status,
    a.current_balance,
    lt.last_transaction_date,
    CASE
        WHEN lt.last_transaction_date IS NULL THEN 'No Activity'
        WHEN julianday((SELECT max_date FROM dataset_max_date))
             - julianday(lt.last_transaction_date) > 90 THEN 'At Risk'
        ELSE 'Engaged'
    END AS engagement_flag
FROM accounts a
LEFT JOIN last_txn lt ON lt.account_id = a.account_id
ORDER BY engagement_flag DESC, a.current_balance DESC
LIMIT 50;

-- ------------------------------------------------------------
-- 5. New account acquisition trend by branch and quarter
-- ------------------------------------------------------------
SELECT
    b.branch_name,
    b.region,
    (strftime('%Y', a.open_date) || '-Q' ||
        ((CAST(strftime('%m', a.open_date) AS INTEGER) - 1) / 3 + 1)) AS open_quarter,
    COUNT(*) AS new_accounts
FROM accounts a
JOIN branches b ON b.branch_id = a.branch_id
GROUP BY b.branch_name, b.region, open_quarter
ORDER BY b.branch_name, open_quarter;
