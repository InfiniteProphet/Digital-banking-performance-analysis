"""
03_build_excel_workbook.py

Builds excel/banking_kpi_summary.xlsx:
    - Branches      (raw data)
    - Accounts      (raw data)
    - Transactions  (raw data, monthly-aggregated for workbook performance)
    - Dashboard     (KPI cards + tables driven by live formulas, not
                      hardcoded Python-computed numbers)

Run: python 03_build_excel_workbook.py
Then recalc with: python /mnt/skills/public/xlsx/scripts/recalc.py <path>
"""

import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "..", "data")
OUT_PATH = os.path.join(BASE, "..", "excel", "banking_kpi_summary.xlsx")

branches = pd.read_csv(os.path.join(DATA_DIR, "branches.csv"))
accounts = pd.read_csv(os.path.join(DATA_DIR, "accounts.csv"))
transactions = pd.read_csv(os.path.join(DATA_DIR, "transactions.csv"))
transactions["txn_month"] = pd.to_datetime(transactions["transaction_date"]).dt.to_period("M").astype(str)

FONT_NAME = "Arial"
HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(name=FONT_NAME, bold=True, color="FFFFFF", size=10)
TITLE_FONT = Font(name=FONT_NAME, bold=True, size=16, color="1F4E79")
KPI_LABEL_FONT = Font(name=FONT_NAME, size=10, color="595959")
KPI_VALUE_FONT = Font(name=FONT_NAME, bold=True, size=18, color="1F4E79")
BODY_FONT = Font(name=FONT_NAME, size=10)
THIN = Side(style="thin", color="D9D9D9")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
KPI_FILL = PatternFill("solid", fgColor="EAF1F8")

wb = Workbook()


def write_table(ws, df, start_row=1, start_col=1):
    """Write a dataframe as a styled table; returns (first_data_row, last_data_row, first_col, last_col)."""
    for j, col in enumerate(df.columns):
        cell = ws.cell(row=start_row, column=start_col + j, value=col)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center")
        cell.border = BORDER
    for i, row in enumerate(df.itertuples(index=False), start=1):
        for j, val in enumerate(row):
            cell = ws.cell(row=start_row + i, column=start_col + j, value=val)
            cell.font = BODY_FONT
            cell.border = BORDER
    first_data_row = start_row + 1
    last_data_row = start_row + len(df)
    first_col = start_col
    last_col = start_col + len(df.columns) - 1
    for j in range(len(df.columns)):
        col_letter = get_column_letter(start_col + j)
        max_len = max([len(str(df.columns[j]))] + [len(str(v)) for v in df.iloc[:, j].astype(str).values[:200]])
        ws.column_dimensions[col_letter].width = min(max(max_len + 2, 10), 40)
    return first_data_row, last_data_row, first_col, last_col


# ---------------------------------------------------------------------------
# Branches sheet
# ---------------------------------------------------------------------------
ws_b = wb.active
ws_b.title = "Branches"
write_table(ws_b, branches)

# ---------------------------------------------------------------------------
# Accounts sheet
# ---------------------------------------------------------------------------
ws_a = wb.create_sheet("Accounts")
acc_first_row, acc_last_row, _, _ = write_table(ws_a, accounts)
# Column map for Accounts: account_id(A) customer_id(B) account_type(C) open_date(D)
# current_balance(E) status(F) branch_id(G)

# ---------------------------------------------------------------------------
# Transactions_Monthly sheet (aggregated for workbook performance;
# raw transactions.csv remains in /data for SQL & Python use)
# ---------------------------------------------------------------------------
monthly = transactions.groupby("txn_month").agg(
    transaction_count=("transaction_id", "count"),
    net_cash_flow=("amount", "sum"),
).reset_index()
fee_monthly = transactions[transactions.transaction_type == "Fee Charge"].groupby("txn_month")["amount"] \
    .apply(lambda s: -s.sum()).reset_index().rename(columns={"amount": "fee_revenue"})
monthly = monthly.merge(fee_monthly, on="txn_month", how="left").fillna(0)
monthly["net_cash_flow"] = monthly["net_cash_flow"].round(2)
monthly["fee_revenue"] = monthly["fee_revenue"].round(2)

ws_t = wb.create_sheet("Transactions_Monthly")
txn_first_row, txn_last_row, _, _ = write_table(ws_t, monthly)
# Columns: txn_month(A) transaction_count(B) net_cash_flow(C) fee_revenue(D)

# ---------------------------------------------------------------------------
# Dashboard sheet — KPI cards driven by formulas referencing the data sheets
# ---------------------------------------------------------------------------
ws_d = wb.create_sheet("Dashboard", 0)
ws_d.sheet_view.showGridLines = False
ws_d["B2"] = "Digital Banking Platform — KPI Dashboard"
ws_d["B2"].font = TITLE_FONT
ws_d["B3"] = "Source: Accounts, Transactions_Monthly (live formulas — recalculates when data changes)"
ws_d["B3"].font = Font(name=FONT_NAME, italic=True, size=9, color="808080")

acc_rng = f"Accounts!E{acc_first_row}:E{acc_last_row}"          # current_balance
acc_status_rng = f"Accounts!F{acc_first_row}:F{acc_last_row}"   # status
acc_type_rng = f"Accounts!C{acc_first_row}:C{acc_last_row}"     # account_type
txn_count_rng = f"Transactions_Monthly!B{txn_first_row}:B{txn_last_row}"
fee_rng = f"Transactions_Monthly!D{txn_first_row}:D{txn_last_row}"

kpi_cards = [
    ("Total Accounts", f"=COUNTA({acc_rng})", "0,0"),
    ("Active Account Rate", f'=COUNTIF({acc_status_rng},"Active")/COUNTA({acc_status_rng})', "0.0%"),
    ("Average Account Balance", f"=AVERAGE({acc_rng})", '"$"#,##0'),
    ("Total Fee Revenue", f"=SUM({fee_rng})", '"$"#,##0'),
    ("Total Transactions (All Months)", f"=SUM({txn_count_rng})", "#,##0"),
]

row = 5
col = 2
for label, formula, num_fmt in kpi_cards:
    c_label = ws_d.cell(row=row, column=col, value=label)
    c_label.font = KPI_LABEL_FONT
    c_val = ws_d.cell(row=row + 1, column=col, value=formula)
    c_val.font = KPI_VALUE_FONT
    c_val.number_format = num_fmt
    for r in (row, row + 1):
        cell = ws_d.cell(row=r, column=col)
        cell.fill = KPI_FILL
        cell.border = BORDER
    ws_d.column_dimensions[get_column_letter(col)].width = 24
    col += 1

# Account type mix table using COUNTIF formulas (not hardcoded)
row2 = row + 4
ws_d.cell(row=row2, column=2, value="Account Type Mix").font = Font(name=FONT_NAME, bold=True, size=12)
hdr_row = row2 + 1
ws_d.cell(row=hdr_row, column=2, value="Account Type").font = HEADER_FONT
ws_d.cell(row=hdr_row, column=2).fill = HEADER_FILL
ws_d.cell(row=hdr_row, column=3, value="Count").font = HEADER_FONT
ws_d.cell(row=hdr_row, column=3).fill = HEADER_FILL
ws_d.cell(row=hdr_row, column=4, value="Avg Balance").font = HEADER_FONT
ws_d.cell(row=hdr_row, column=4).fill = HEADER_FILL

acc_types = sorted(accounts["account_type"].unique())
for i, atype in enumerate(acc_types):
    r = hdr_row + 1 + i
    ws_d.cell(row=r, column=2, value=atype).font = BODY_FONT
    ws_d.cell(row=r, column=3, value=f'=COUNTIF({acc_type_rng},B{r})').font = BODY_FONT
    ws_d.cell(row=r, column=3).number_format = "#,##0"
    ws_d.cell(row=r, column=4, value=f'=AVERAGEIF({acc_type_rng},B{r},{acc_rng})').font = BODY_FONT
    ws_d.cell(row=r, column=4).number_format = '"$"#,##0'
    for c in (2, 3, 4):
        ws_d.cell(row=r, column=c).border = BORDER

ws_d.column_dimensions["A"].width = 3

# Legend note (per skill: document assumptions / data source)
note_row = hdr_row + 1 + len(acc_types) + 2
ws_d.cell(row=note_row, column=2,
          value="Note: Transactions_Monthly is a monthly aggregate of the full transaction log "
                "(see /data/transactions.csv and /sql for full granular analysis).").font = \
    Font(name=FONT_NAME, italic=True, size=9, color="808080")

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
wb.save(OUT_PATH)
print(f"Workbook saved to {OUT_PATH}")
