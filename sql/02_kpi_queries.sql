/* ============================================================
   02_kpi_queries.sql
   Core KPI queries: transaction trends, customer behavior,
   branch performance, and account activity.
   ============================================================ */

-- ------------------------------------------------------------
-- KPI 1: Monthly transaction volume & net cash flow trend
-- ------------------------------------------------------------
SELECT
    strftime('%Y-%m', transaction_date) AS txn_month,
    COUNT(*)                             AS transaction_count,
    ROUND(SUM(amount), 2)                AS net_cash_flow,
    ROUND(AVG(amount), 2)                AS avg_transaction_amount
FROM transactions
GROUP BY txn_month
ORDER BY txn_month;

-- ------------------------------------------------------------
-- KPI 2: Revenue-relevant transactions (fees) by month
-- Proxy for fee revenue opportunity tracking
-- ------------------------------------------------------------
SELECT
    strftime('%Y-%m', transaction_date) AS txn_month,
    COUNT(*)                             AS fee_transaction_count,
    ROUND(SUM(-amount), 2)               AS fee_revenue
FROM transactions
WHERE transaction_type = 'Fee Charge'
GROUP BY txn_month
ORDER BY txn_month;

-- ------------------------------------------------------------
-- KPI 3: Branch performance leaderboard
-- Transaction volume, revenue, and active accounts per branch
-- ------------------------------------------------------------
SELECT
    b.branch_id,
    b.branch_name,
    b.region,
    COUNT(DISTINCT a.account_id)                          AS total_accounts,
    COUNT(DISTINCT CASE WHEN a.status = 'Active'
                         THEN a.account_id END)            AS active_accounts,
    COUNT(t.transaction_id)                                AS total_transactions,
    ROUND(SUM(CASE WHEN t.transaction_type = 'Fee Charge'
                    THEN -t.amount ELSE 0 END), 2)          AS fee_revenue,
    ROUND(AVG(a.current_balance), 2)                        AS avg_account_balance
FROM branches b
LEFT JOIN accounts a      ON a.branch_id = b.branch_id
LEFT JOIN transactions t  ON t.branch_id = b.branch_id
GROUP BY b.branch_id, b.branch_name, b.region
ORDER BY total_transactions DESC;

-- ------------------------------------------------------------
-- KPI 4: Customer segment behavior
-- Average balance, transaction frequency, and revenue by segment
-- ------------------------------------------------------------
SELECT
    c.segment,
    COUNT(DISTINCT c.customer_id)                          AS customers,
    ROUND(AVG(a.current_balance), 2)                        AS avg_balance,
    COUNT(t.transaction_id)                                 AS total_transactions,
    ROUND(COUNT(t.transaction_id) * 1.0
          / COUNT(DISTINCT c.customer_id), 2)                AS avg_transactions_per_customer,
    ROUND(SUM(CASE WHEN t.transaction_type = 'Fee Charge'
                    THEN -t.amount ELSE 0 END), 2)           AS fee_revenue
FROM customers c
JOIN accounts a       ON a.customer_id = c.customer_id
LEFT JOIN transactions t ON t.customer_id = c.customer_id
GROUP BY c.segment
ORDER BY fee_revenue DESC;

-- ------------------------------------------------------------
-- KPI 5: Account activity / dormancy overview
-- Identifies dormant accounts as a re-engagement / revenue opportunity
-- ------------------------------------------------------------
SELECT
    account_type,
    status,
    COUNT(*)                       AS account_count,
    ROUND(AVG(current_balance), 2) AS avg_balance,
    ROUND(SUM(current_balance), 2) AS total_balance
FROM accounts
GROUP BY account_type, status
ORDER BY account_type, status;

-- ------------------------------------------------------------
-- KPI 6: Channel adoption (digital vs. in-person)
-- ------------------------------------------------------------
SELECT
    channel,
    COUNT(*)                                            AS transaction_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM transactions), 2) AS pct_of_total
FROM transactions
GROUP BY channel
ORDER BY transaction_count DESC;

-- ------------------------------------------------------------
-- KPI 7: Top 10 customers by transaction volume (engagement)
-- ------------------------------------------------------------
SELECT
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.segment,
    COUNT(t.transaction_id)            AS transaction_count,
    ROUND(SUM(t.amount), 2)            AS net_amount
FROM customers c
JOIN transactions t ON t.customer_id = c.customer_id
GROUP BY c.customer_id, customer_name, c.segment
ORDER BY transaction_count DESC
LIMIT 10;
