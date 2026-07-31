/* ============================================================
   01_schema.sql
   Schema for the Digital Banking Platform analysis database.
   Compatible with SQLite / PostgreSQL / MySQL (minor type tweaks
   may be needed for MySQL, e.g. DATE vs TEXT for dates in SQLite).
   ============================================================ */

DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS branches;

CREATE TABLE branches (
    branch_id     TEXT PRIMARY KEY,
    branch_name   TEXT NOT NULL,
    city          TEXT NOT NULL,
    region        TEXT NOT NULL,
    open_date     DATE NOT NULL,
    staff_count   INTEGER NOT NULL
);

CREATE TABLE customers (
    customer_id     TEXT PRIMARY KEY,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    age             INTEGER NOT NULL,
    segment         TEXT NOT NULL,             -- Retail / Premium / Business
    home_branch_id  TEXT NOT NULL REFERENCES branches(branch_id),
    signup_date     DATE NOT NULL,
    credit_score    INTEGER NOT NULL
);

CREATE TABLE accounts (
    account_id       TEXT PRIMARY KEY,
    customer_id      TEXT NOT NULL REFERENCES customers(customer_id),
    account_type     TEXT NOT NULL,             -- Checking / Savings / Money Market / Business
    open_date        DATE NOT NULL,
    current_balance  DECIMAL(14,2) NOT NULL,
    status           TEXT NOT NULL,             -- Active / Dormant
    branch_id        TEXT NOT NULL REFERENCES branches(branch_id)
);

CREATE TABLE transactions (
    transaction_id     TEXT PRIMARY KEY,
    account_id         TEXT NOT NULL REFERENCES accounts(account_id),
    customer_id        TEXT NOT NULL REFERENCES customers(customer_id),
    branch_id          TEXT NOT NULL REFERENCES branches(branch_id),
    transaction_date   DATETIME NOT NULL,
    transaction_type   TEXT NOT NULL,           -- Deposit / Withdrawal / Transfer / etc.
    channel             TEXT NOT NULL,          -- Mobile App / Web Banking / Branch / ATM / Call Center
    amount              DECIMAL(14,2) NOT NULL  -- negative = outflow, positive = inflow
);

-- Helpful indexes for the analysis queries in 02 and 03
CREATE INDEX idx_txn_account   ON transactions(account_id);
CREATE INDEX idx_txn_branch    ON transactions(branch_id);
CREATE INDEX idx_txn_date      ON transactions(transaction_date);
CREATE INDEX idx_accounts_cust ON accounts(customer_id);
CREATE INDEX idx_accounts_br   ON accounts(branch_id);
