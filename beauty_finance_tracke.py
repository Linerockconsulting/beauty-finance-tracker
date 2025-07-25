import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1️⃣ --- CONFIGS ---
st.set_page_config(page_title="Beauty Finance Tracker 💄", layout="wide")

# 2️⃣ --- AUTH ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
client = gspread.authorize(creds)
sheet = client.open("BeautyFinanceData")
income_sheet = sheet.worksheet("Income")
expense_sheet = sheet.worksheet("Expenses")

# 3️⃣ --- FETCH DATA ---
income_data = income_sheet.get_all_values()[1:]  # Skip header
expense_data = expense_sheet.get_all_values()[1:]  # Skip header

income_df = pd.DataFrame(income_data, columns=["Date", "Client", "Service", "Amount", "Notes"])
expense_df = pd.DataFrame(expense_data, columns=["Date", "Category", "Amount", "Notes"])

income_df["Amount"] = pd.to_numeric(income_df["Amount"], errors="coerce").fillna(0)
expense_df["Amount"] = pd.to_numeric(expense_df["Amount"], errors="coerce").fillna(0)

# 4️⃣ --- PAGE NAVIGATION ---
st.title("💄 Beauty Finance Tracker")
st.markdown("Effortlessly track your income and expenses for your beauty business 💼")
st.markdown("---")

tab = st.selectbox("📍 Select a page", ["📊 Dashboard", "➕ Add Entry", "📁 View Report"])

# 5️⃣ --- DASHBOARD ---
if tab == "📊 Dashboard":
    total_income = income_df["Amount"].sum()
    total_expense = expense_df["Amount"].sum()
    net_profit = total_income - total_expense

    st.markdown("## 💹 Business Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Income", f"₹{total_income:,.2f}")
    col2.metric("💸 Total Expenses", f"₹{total_expense:,.2f}")
    col3.metric("📈 Net Profit", f"₹{net_profit:,.2f}", delta=f"{net_profit - total_expense:,.2f}")

    st.markdown("### 📅 Recent Entries")
    st.write("#### Income")
    st.dataframe(income_df.tail(5), use_container_width=True)

    st.write("#### Expenses")
    st.dataframe(expense_df.tail(5), use_container_width=True)

# 6️⃣ --- ADD ENTRY ---
elif tab == "➕ Add Entry":
    st.markdown("## ➕ Add New Entry")

    entry_type = st.radio("Select type", ["Income", "Expense"], horizontal=True)
    with st.form("entry_form"):
        date = st.date_input("Date", datetime.date.today())
        if entry_type == "Income":
            client = st.text_input("Client Name")
            service = st.text_input("Service Type")
            amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
            notes = st.text_input("Notes")
        else:
            category = st.text_input("Expense Category")
            amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
            notes = st.text_input("Notes")

        submitted = st.form_submit_button("✅ Submit")

        if submitted:
            row = [str(date), client if entry_type == "Income" else category, service if entry_type == "Income" else "", amount, notes]
            if entry_type == "Income":
                income_sheet.append_row(row)
            else:
                expense_sheet.append_row(row)
            st.success(f"{entry_type} entry added successfully!")

# 7️⃣ --- REPORT VIEW ---
elif tab == "📁 View Report":
    st.markdown("## 📁 Full Financial Report")
    st.markdown("### 💰 Income Report")
    st.dataframe(income_df, use_container_width=True)
    st.download_button("⬇️ Download Income CSV", income_df.to_csv(index=False), file_name="income_report.csv")

    st.markdown("### 💸 Expense Report")
    st.dataframe(expense_df, use_container_width=True)
    st.download_button("⬇️ Download Expense CSV", expense_df.to_csv(index=False), file_name="expense_report.csv")
