"""
02_eda_analysis.py

Exploratory data analysis and KPI computation for the digital banking
dataset. Reads the CSVs produced by 01_data_generation.py, computes key
business metrics, and saves chart images to ../images/ for use in the
README / portfolio write-up.

Run: python 02_eda_analysis.py
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "..", "data")
IMG_DIR = os.path.join(BASE, "..", "images")
os.makedirs(IMG_DIR, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 130,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "font.size": 10,
})
COLOR_PRIMARY = "#1f4e79"
COLOR_ACCENT = "#2ca02c"
COLOR_WARN = "#d62728"

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
branches = pd.read_csv(os.path.join(DATA_DIR, "branches.csv"))
customers = pd.read_csv(os.path.join(DATA_DIR, "customers.csv"), parse_dates=["signup_date"])
accounts = pd.read_csv(os.path.join(DATA_DIR, "accounts.csv"), parse_dates=["open_date"])
transactions = pd.read_csv(os.path.join(DATA_DIR, "transactions.csv"), parse_dates=["transaction_date"])

transactions["txn_month"] = transactions["transaction_date"].dt.to_period("M").astype(str)

# ---------------------------------------------------------------------------
# KPI 1: Monthly transaction volume & net cash flow
# ---------------------------------------------------------------------------
monthly = transactions.groupby("txn_month").agg(
    transaction_count=("transaction_id", "count"),
    net_cash_flow=("amount", "sum"),
).reset_index()

fig, ax1 = plt.subplots(figsize=(9, 4.5))
ax1.bar(monthly["txn_month"], monthly["transaction_count"], color=COLOR_PRIMARY, alpha=0.85)
ax1.set_ylabel("Transaction Count", color=COLOR_PRIMARY)
ax1.tick_params(axis="x", rotation=60)
ax1.set_title("Monthly Transaction Volume", fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(os.path.join(IMG_DIR, "monthly_transaction_volume.png"))
plt.close(fig)

# ---------------------------------------------------------------------------
# KPI 2: Branch performance leaderboard
# ---------------------------------------------------------------------------
branch_txn = transactions.merge(accounts[["account_id", "branch_id"]], on="branch_id", how="left") \
    if "branch_id" in transactions.columns else transactions
branch_perf = transactions.groupby("branch_id").agg(total_transactions=("transaction_id", "count")).reset_index()
branch_perf = branch_perf.merge(branches[["branch_id", "branch_name", "region"]], on="branch_id")
branch_perf = branch_perf.sort_values("total_transactions", ascending=True)

fig, ax = plt.subplots(figsize=(8, 6))
ax.barh(branch_perf["branch_name"], branch_perf["total_transactions"], color=COLOR_PRIMARY)
ax.set_title("Branch Performance: Total Transactions", fontsize=13, fontweight="bold")
ax.set_xlabel("Transaction Count")
fig.tight_layout()
fig.savefig(os.path.join(IMG_DIR, "branch_performance.png"))
plt.close(fig)

# ---------------------------------------------------------------------------
# KPI 3: Customer segment behavior
# ---------------------------------------------------------------------------
acct_cust = accounts.merge(customers[["customer_id", "segment"]], on="customer_id")
seg_balance = acct_cust.groupby("segment")["current_balance"].mean().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(6, 4.5))
bars = ax.bar(seg_balance.index, seg_balance.values, color=[COLOR_PRIMARY, COLOR_ACCENT, "#f0ad4e"])
ax.set_title("Average Account Balance by Customer Segment", fontsize=13, fontweight="bold")
ax.set_ylabel("Avg Balance ($)")
ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
for b in bars:
    ax.annotate(f"${b.get_height():,.0f}", (b.get_x() + b.get_width() / 2, b.get_height()),
                ha="center", va="bottom", fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(IMG_DIR, "segment_avg_balance.png"))
plt.close(fig)

# ---------------------------------------------------------------------------
# KPI 4: Account activity / dormancy overview
# ---------------------------------------------------------------------------
status_counts = accounts["status"].value_counts()

fig, ax = plt.subplots(figsize=(5, 5))
colors = [COLOR_ACCENT if s == "Active" else COLOR_WARN for s in status_counts.index]
ax.pie(status_counts.values, labels=status_counts.index, autopct="%1.1f%%",
       colors=colors, startangle=90, wedgeprops={"edgecolor": "white", "linewidth": 1.5})
ax.set_title("Account Activity: Active vs. Dormant", fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(os.path.join(IMG_DIR, "account_dormancy.png"))
plt.close(fig)

# ---------------------------------------------------------------------------
# KPI 5: Channel adoption
# ---------------------------------------------------------------------------
channel_counts = transactions["channel"].value_counts().sort_values(ascending=True)

fig, ax = plt.subplots(figsize=(7, 4.5))
ax.barh(channel_counts.index, channel_counts.values, color=COLOR_PRIMARY)
ax.set_title("Transaction Volume by Channel", fontsize=13, fontweight="bold")
ax.set_xlabel("Transaction Count")
fig.tight_layout()
fig.savefig(os.path.join(IMG_DIR, "channel_adoption.png"))
plt.close(fig)

# ---------------------------------------------------------------------------
# Console KPI summary (also useful for README stats)
# ---------------------------------------------------------------------------
total_customers = len(customers)
total_accounts = len(accounts)
active_rate = (accounts["status"] == "Active").mean() * 100
total_txns = len(transactions)
fee_revenue = -transactions.loc[transactions.transaction_type == "Fee Charge", "amount"].sum()
avg_balance = accounts["current_balance"].mean()
digital_share = transactions["channel"].isin(["Mobile App", "Web Banking"]).mean() * 100

print("=" * 55)
print("DIGITAL BANKING PLATFORM — KPI SUMMARY")
print("=" * 55)
print(f"Total Customers:            {total_customers:,}")
print(f"Total Accounts:             {total_accounts:,}")
print(f"Active Account Rate:        {active_rate:.1f}%")
print(f"Total Transactions:         {total_txns:,}")
print(f"Total Fee Revenue:          ${fee_revenue:,.2f}")
print(f"Average Account Balance:    ${avg_balance:,.2f}")
print(f"Digital Channel Share:      {digital_share:.1f}%  (Mobile App + Web Banking)")
print("=" * 55)
print(f"\nCharts saved to: {os.path.abspath(IMG_DIR)}")
