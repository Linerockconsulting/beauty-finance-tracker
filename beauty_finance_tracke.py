# beauty_finance_tracker.py

import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Beauty Biz Finance Tracker", layout="centered")

# Initialize session state
if 'income_data' not in st.session_state:
    st.session_state['income_data'] = []
if 'expense_data' not in st.session_state:
    st.session_state['expense_data'] = []

st.title("💅 Beauty Biz Finance Tracker")

menu = st.sidebar.radio("Go to", ["📊 Dashboard", "➕ Add Entry", "📈 View Report"])

# --- Dashboard ---
if menu == "📊 Dashboard":
    st.header("📊 Finance Summary")

    income_df = pd.DataFrame(st.session_state['income_data'], columns=["Date", "Client", "Service", "Amount"])
    expense_df = pd.DataFrame(st.session_state['expense_data'], columns=["Date", "Type", "Amount"])

    total_income = income_df["Amount"].sum() if not income_df.empty else 0
    total_expense = expense_df["Amount"].sum() if not expense_df.empty else 0
    profit = total_income - total_expense

    st.metric("Total Income", f"₹ {total_income}")
    st.metric("Total Expenses", f"₹ {total_expense}")
    st.metric("Net Profit", f"₹ {profit}")

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
            notes = st.text_area("Notes (optional)")
            submitted = st.form_submit_button("Add Income")
            if submitted:
                st.session_state['income_data'].append([date, client, service, amount])
                st.success("Income added!")

    else:
        with st.form("expense_form"):
            date = st.date_input("Date", value=datetime.today())
            exp_type = st.text_input("Expense Type")
            amount = st.number_input("Amount (₹)", min_value=0.0)
            notes = st.text_area("Notes (optional)")
            submitted = st.form_submit_button("Add Expense")
            if submitted:
                st.session_state['expense_data'].append([date, exp_type, amount])
                st.success("Expense added!")

# --- View Report ---
elif menu == "📈 View Report":
    st.header("📈 Finance Report")

    st.subheader("Income Entries")
    income_df = pd.DataFrame(st.session_state['income_data'], columns=["Date", "Client", "Service", "Amount"])
    st.dataframe(income_df)
    st.download_button("Download Income CSV", income_df.to_csv(index=False), "income.csv")

    st.subheader("Expense Entries")
    expense_df = pd.DataFrame(st.session_state['expense_data'], columns=["Date", "Type", "Amount"])
    st.dataframe(expense_df)
    st.download_button("Download Expense CSV", expense_df.to_csv(index=False), "expenses.csv")
