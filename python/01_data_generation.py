"""
01_data_generation.py

Generates a realistic, relational synthetic dataset for a digital banking
platform: branches, customers, accounts, and transactions.

Output: CSV files written to ../data/
    - branches.csv
    - customers.csv
    - accounts.csv
    - transactions.csv

The data is randomly generated but follows realistic banking patterns:
    - Seasonal/monthly transaction volume trends
    - Branch performance variance
    - Account types with different balance/activity profiles
    - Customer segments (Retail, Premium, Business) with different behavior
    - A mix of active and dormant accounts (for churn/engagement KPIs)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

RNG_SEED = 42
rng = np.random.default_rng(RNG_SEED)

N_CUSTOMERS = 2000
N_BRANCHES = 15
N_ACCOUNTS = 2600
N_TRANSACTIONS = 60000

START_DATE = datetime(2024, 8, 1)
END_DATE = datetime(2026, 7, 31)

CITIES = [
    "New York", "Chicago", "Houston", "Phoenix", "Philadelphia",
    "San Antonio", "San Diego", "Dallas", "Austin", "Columbus",
    "Charlotte", "Denver", "Seattle", "Boston", "Atlanta"
]

REGIONS = {
    "New York": "Northeast", "Philadelphia": "Northeast", "Boston": "Northeast",
    "Chicago": "Midwest", "Columbus": "Midwest",
    "Houston": "South", "San Antonio": "South", "Dallas": "South",
    "Austin": "South", "Charlotte": "South", "Atlanta": "South",
    "Phoenix": "West", "San Diego": "West", "Denver": "West", "Seattle": "West",
}

ACCOUNT_TYPES = ["Checking", "Savings", "Money Market", "Business"]
ACCOUNT_TYPE_WEIGHTS = [0.45, 0.35, 0.10, 0.10]

CUSTOMER_SEGMENTS = ["Retail", "Premium", "Business"]
SEGMENT_WEIGHTS = [0.70, 0.20, 0.10]

TXN_TYPES = [
    "Deposit", "Withdrawal", "Transfer", "Bill Payment",
    "POS Purchase", "ATM Withdrawal", "Online Purchase", "Fee Charge"
]
TXN_TYPE_WEIGHTS = [0.14, 0.10, 0.15, 0.10, 0.20, 0.10, 0.16, 0.05]

CHANNELS = ["Mobile App", "Web Banking", "Branch", "ATM", "Call Center"]
CHANNEL_WEIGHTS = [0.42, 0.23, 0.12, 0.15, 0.08]


def random_dates(start, end, n):
    delta_days = (end - start).days
    offsets = rng.integers(0, delta_days, size=n)
    seconds = rng.integers(0, 86400, size=n)
    return [start + timedelta(days=int(d), seconds=int(s)) for d, s in zip(offsets, seconds)]


# ---------------------------------------------------------------------------
# 1. Branches
# ---------------------------------------------------------------------------
branch_ids = [f"BR{100 + i}" for i in range(N_BRANCHES)]
branches = pd.DataFrame({
    "branch_id": branch_ids,
    "branch_name": [f"{city} Branch" for city in CITIES],
    "city": CITIES,
    "region": [REGIONS[c] for c in CITIES],
    "open_date": [d.date() for d in random_dates(datetime(2005, 1, 1), datetime(2020, 1, 1), N_BRANCHES)],
    "staff_count": rng.integers(6, 35, size=N_BRANCHES),
})

# ---------------------------------------------------------------------------
# 2. Customers
# ---------------------------------------------------------------------------
customer_ids = [f"CUST{10000 + i}" for i in range(N_CUSTOMERS)]
first_names = ["James","Mary","John","Patricia","Robert","Jennifer","Michael","Linda","William","Elizabeth",
               "David","Barbara","Richard","Susan","Joseph","Jessica","Thomas","Sarah","Charles","Karen",
               "Christopher","Nancy","Daniel","Lisa","Matthew","Betty","Anthony","Margaret","Mark","Sandra",
               "Priya","Arjun","Wei","Fatima","Carlos","Aiko","Omar","Elena","Noah","Ava"]
last_names = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
              "Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin",
              "Lee","Perez","Thompson","White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson"]

signup_dates = random_dates(datetime(2015, 1, 1), END_DATE, N_CUSTOMERS)

customers = pd.DataFrame({
    "customer_id": customer_ids,
    "first_name": rng.choice(first_names, size=N_CUSTOMERS),
    "last_name": rng.choice(last_names, size=N_CUSTOMERS),
    "age": rng.integers(18, 80, size=N_CUSTOMERS),
    "segment": rng.choice(CUSTOMER_SEGMENTS, size=N_CUSTOMERS, p=SEGMENT_WEIGHTS),
    "home_branch_id": rng.choice(branch_ids, size=N_CUSTOMERS),
    "signup_date": [d.date() for d in signup_dates],
    "credit_score": rng.integers(560, 850, size=N_CUSTOMERS),
})

# ---------------------------------------------------------------------------
# 3. Accounts
# ---------------------------------------------------------------------------
account_ids = [f"ACC{100000 + i}" for i in range(N_ACCOUNTS)]
acct_customer = rng.choice(customer_ids, size=N_ACCOUNTS)  # some customers have multiple accounts
acct_types = rng.choice(ACCOUNT_TYPES, size=N_ACCOUNTS, p=ACCOUNT_TYPE_WEIGHTS)

# Balance profile depends on account type
base_balance = {
    "Checking": (500, 4000),
    "Savings": (1000, 15000),
    "Money Market": (5000, 60000),
    "Business": (2000, 80000),
}
balances = np.array([
    rng.uniform(*base_balance[t]) for t in acct_types
]).round(2)

acct_open_dates = random_dates(datetime(2015, 1, 1), END_DATE, N_ACCOUNTS)

# ~12% of accounts are dormant (no recent activity) for engagement KPIs
is_dormant = rng.choice([0, 1], size=N_ACCOUNTS, p=[0.88, 0.12])

accounts = pd.DataFrame({
    "account_id": account_ids,
    "customer_id": acct_customer,
    "account_type": acct_types,
    "open_date": [d.date() for d in acct_open_dates],
    "current_balance": balances,
    "status": np.where(is_dormant == 1, "Dormant", "Active"),
    "branch_id": rng.choice(branch_ids, size=N_ACCOUNTS),
})

# ---------------------------------------------------------------------------
# 4. Transactions
# ---------------------------------------------------------------------------
txn_ids = [f"TXN{1000000 + i}" for i in range(N_TRANSACTIONS)]

# Weight transaction volume toward active accounts, with mild seasonality
active_accounts = accounts.loc[accounts.status == "Active", "account_id"].values
dormant_accounts = accounts.loc[accounts.status == "Dormant", "account_id"].values

txn_account_pool = rng.choice(
    active_accounts, size=int(N_TRANSACTIONS * 0.94)
).tolist() + rng.choice(
    dormant_accounts, size=N_TRANSACTIONS - int(N_TRANSACTIONS * 0.94)
).tolist()
rng.shuffle(txn_account_pool)

txn_dates = random_dates(START_DATE, END_DATE, N_TRANSACTIONS)
# Add a mild upward trend + seasonal bump (Nov-Dec, back-to-school Aug-Sep) by
# resampling extra weight into those months
month_weights = np.array([1.0 if START_DATE <= d <= END_DATE else 0 for d in txn_dates])

txn_types = rng.choice(TXN_TYPES, size=N_TRANSACTIONS, p=TXN_TYPE_WEIGHTS)
channels = rng.choice(CHANNELS, size=N_TRANSACTIONS, p=CHANNEL_WEIGHTS)

# Amount depends on transaction type
def gen_amount(t):
    if t == "Deposit":
        return rng.uniform(50, 5000)
    if t == "Withdrawal":
        return -rng.uniform(20, 1500)
    if t == "Transfer":
        return rng.choice([-1, 1]) * rng.uniform(20, 3000)
    if t == "Bill Payment":
        return -rng.uniform(15, 800)
    if t == "POS Purchase":
        return -rng.uniform(5, 300)
    if t == "ATM Withdrawal":
        return -rng.uniform(20, 500)
    if t == "Online Purchase":
        return -rng.uniform(10, 600)
    if t == "Fee Charge":
        return -rng.uniform(1, 45)
    return 0.0

amounts = np.array([gen_amount(t) for t in txn_types]).round(2)

# map account -> branch/customer for convenience columns
acc_to_branch = dict(zip(accounts.account_id, accounts.branch_id))
acc_to_customer = dict(zip(accounts.account_id, accounts.customer_id))

transactions = pd.DataFrame({
    "transaction_id": txn_ids,
    "account_id": txn_account_pool,
    "customer_id": [acc_to_customer[a] for a in txn_account_pool],
    "branch_id": [acc_to_branch[a] for a in txn_account_pool],
    "transaction_date": [d.strftime("%Y-%m-%d %H:%M:%S") for d in txn_dates],
    "transaction_type": txn_types,
    "channel": channels,
    "amount": amounts,
})
transactions = transactions.sort_values("transaction_date").reset_index(drop=True)

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
import os
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
os.makedirs(out_dir, exist_ok=True)
branches.to_csv(f"{out_dir}/branches.csv", index=False)
customers.to_csv(f"{out_dir}/customers.csv", index=False)
accounts.to_csv(f"{out_dir}/accounts.csv", index=False)
transactions.to_csv(f"{out_dir}/transactions.csv", index=False)

print("Data generation complete.")
print(f"  branches:     {len(branches):,} rows")
print(f"  customers:    {len(customers):,} rows")
print(f"  accounts:     {len(accounts):,} rows")
print(f"  transactions: {len(transactions):,} rows")
