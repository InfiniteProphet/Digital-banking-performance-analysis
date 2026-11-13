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
-- Aggregate accounts and transactions separately to avoid join fan-out.
-- ------------------------------------------------------------
WITH account_metrics AS (
    SELECT
        branch_id,
        COUNT(*) AS total_accounts,
        SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) AS active_accounts,
        AVG(current_balance) AS avg_account_balance
    FROM accounts
    GROUP BY branch_id
),
transaction_metrics AS (
    SELECT
        branch_id,
        COUNT(*) AS total_transactions,
        SUM(CASE WHEN transaction_type = 'Fee Charge' THEN -amount ELSE 0 END) AS fee_revenue
    FROM transactions
    GROUP BY branch_id
)
SELECT
    b.branch_id,
    b.branch_name,
    b.region,
    COALESCE(a.total_accounts, 0) AS total_accounts,
    COALESCE(a.active_accounts, 0) AS active_accounts,
    COALESCE(t.total_transactions, 0) AS total_transactions,
    ROUND(COALESCE(t.fee_revenue, 0), 2) AS fee_revenue,
    ROUND(a.avg_account_balance, 2) AS avg_account_balance
FROM branches b
LEFT JOIN account_metrics a ON a.branch_id = b.branch_id
LEFT JOIN transaction_metrics t ON t.branch_id = b.branch_id
ORDER BY total_transactions DESC;

-- ------------------------------------------------------------
-- KPI 4: Customer segment behavior
-- Aggregate customer balances and transactions independently to avoid
-- multiplying account balances when a customer has multiple transactions.
-- ------------------------------------------------------------
WITH customer_balances AS (
    SELECT
        customer_id,
        SUM(current_balance) AS total_balance
    FROM accounts
    GROUP BY customer_id
),
customer_activity AS (
    SELECT
        customer_id,
        COUNT(*) AS total_transactions,
        SUM(CASE WHEN transaction_type = 'Fee Charge' THEN -amount ELSE 0 END) AS fee_revenue
    FROM transactions
    GROUP BY customer_id
)
SELECT
    c.segment,
    COUNT(*) AS customers,
    ROUND(AVG(COALESCE(cb.total_balance, 0)), 2) AS avg_customer_balance,
    SUM(COALESCE(ca.total_transactions, 0)) AS total_transactions,
    ROUND(
        SUM(COALESCE(ca.total_transactions, 0)) * 1.0 / COUNT(*), 2
    ) AS avg_transactions_per_customer,
    ROUND(SUM(COALESCE(ca.fee_revenue, 0)), 2) AS fee_revenue
FROM customers c
LEFT JOIN customer_balances cb ON cb.customer_id = c.customer_id
LEFT JOIN customer_activity ca ON ca.customer_id = c.customer_id
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
