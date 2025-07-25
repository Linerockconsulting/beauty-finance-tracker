# beauty_finance_tracker.py

import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Beauty Biz Finance Tracker", layout="centered")
st.title("💅 Beauty Biz Finance Tracker")

# --- Google Sheets Setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
client = gspread.authorize(creds)

# ✅ Using your actual Google Sheet ID
spreadsheet_id = "1zhx8YZ48h3qhRRaxk8pfntzNodJ0rjNWPKiWrNKfdk8"
sheet = client.open_by_key(spreadsheet_id)

income_sheet = sheet.worksheet("Income")
expense_sheet = sheet.worksheet("Expenses")

# --- Helper Functions ---

def load_data():
    # Skip header, and keep only rows with exactly 4 columns for income, 3 for expense
    raw_income = income_sheet.get_all_values()[1:]
    raw_expense = expense_sheet.get_all_values()[1:]

    income_data = [row for row in raw_income if len(row) == 4]
    expense_data = [row for row in raw_expense if len(row) == 3]

    return income_data, expense_data


def add_income(date, client, service, amount):
    income_sheet.append_row([str(date), client, service, str(amount)])

def add_expense(date, exp_type, amount):
    expense_sheet.append_row([str(date), exp_type, str(amount)])

# --- Menu ---
menu = st.sidebar.radio("Go to", ["📊 Dashboard", "➕ Add Entry", "📈 View Report"])
income_data, expense_data = load_data()
st.write("✅ Raw Income Data:", income_data)
st.write("✅ Raw Expense Data:", expense_data)




# --- Dashboard ---
if menu == "📊 Dashboard":
    st.header("📊 Finance Summary")
    income_df = pd.DataFrame(income_data, columns=["Date", "Client", "Service", "Amount"])
    expense_df = pd.DataFrame(expense_data, columns=["Date", "Type", "Amount"])

    income_df["Amount"] = pd.to_numeric(income_df["Amount"], errors="coerce").fillna(0)
    expense_df["Amount"] = pd.to_numeric(expense_df["Amount"], errors="coerce").fillna(0)

    st.metric("Total Income", f"₹ {income_df['Amount'].sum():,.2f}")
    st.metric("Total Expenses", f"₹ {expense_df['Amount'].sum():,.2f}")
    st.metric("Net Profit", f"₹ {(income_df['Amount'].sum() - expense_df['Amount'].sum()):,.2f}")

# --- Add Entry ---
elif menu == "➕ Add Entry":
    st.header("➕ Add Income or Expense")
    entry_type = st.radio("Entry Type", ["Income", "Expense"])

    if entry_type == "Income":
        with st.form("income_form"):
            date = st.date_input("Date", value=datetime.today())
            client = st.text_input("Client Name")
            service = st.text_input("Service")
            amount = st.number_input("Amount (₹)", min_value=0.0)
            submitted = st.form_submit_button("Add Income")
            if submitted:
                add_income(date, client, service, amount)
                st.success("Income added to Google Sheet!")

    else:
        with st.form("expense_form"):
            date = st.date_input("Date", value=datetime.today())
            exp_type = st.text_input("Expense Type")
            amount = st.number_input("Amount (₹)", min_value=0.0)
            submitted = st.form_submit_button("Add Expense")
            if submitted:
                add_expense(date, exp_type, amount)
                st.success("Expense added to Google Sheet!")

# --- View Report ---
elif menu == "📈 View Report":
    st.header("📈 Finance Report")
    st.subheader("Income Entries")
    income_df = pd.DataFrame(income_data, columns=["Date", "Client", "Service", "Amount"])
    st.dataframe(income_df)
    st.download_button("Download Income CSV", income_df.to_csv(index=False), "income.csv")

    st.subheader("Expense Entries")
    expense_df = pd.DataFrame(expense_data, columns=["Date", "Type", "Amount"])
    st.dataframe(expense_df)
    st.download_button("Download Expense CSV", expense_df.to_csv(index=False), "expenses.csv")
