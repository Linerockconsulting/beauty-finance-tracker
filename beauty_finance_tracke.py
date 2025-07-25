from xhtml2pdf import pisa
import io
import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- PDF Generation ---
def generate_pdf_from_html(html: str):
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(html), dest=result)
    if pisa_status.err:
        return None
    return result.getvalue()

# --- Streamlit Page Config ---
st.set_page_config(page_title="B-Keepers Finance ERP", layout="wide")
st.title("💼 B-Keepers Finance ERP")
st.markdown("Effortlessly track your income and expenses for your beauty business")

# --- Google Sheets Auth ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
client = gspread.authorize(creds)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1zhx8YZ48h3qhRRaxk8pfntzNodJ0rjNWPKiWrNKfdk8/edit")

# --- Load Worksheets ---
income_sheet = sheet.worksheet("Income")
expense_sheet = sheet.worksheet("Expenses")
try:
    customer_sheet = sheet.worksheet("Customers")
except gspread.exceptions.WorksheetNotFound:
    customer_sheet = sheet.add_worksheet(title="Customers", rows="100", cols="2")
    customer_sheet.append_row(["Customer Code", "Client Name"])

# --- Fetch Data ---
income_data = income_sheet.get_all_values()[1:]
expense_data = expense_sheet.get_all_values()[1:]
customer_data = customer_sheet.get_all_values()[1:]

income_df = pd.DataFrame(income_data, columns=["Date", "Client", "Service", "Amount", "Notes"])
expense_df = pd.DataFrame(expense_data, columns=["Date", "Category", "Amount", "Notes"])
customer_df = pd.DataFrame(customer_data, columns=["Customer Code", "Client Name"]) if customer_data else pd.DataFrame(columns=["Customer Code", "Client Name"])

# Clean & Convert
income_df["Amount"] = pd.to_numeric(income_df["Amount"], errors="coerce").fillna(0)
expense_df["Amount"] = pd.to_numeric(expense_df["Amount"], errors="coerce").fillna(0)
existing_clients = customer_df["Client Name"].tolist()

# --- Page Navigation ---
tab = st.selectbox("📍 Select a page", ["📊 Dashboard", "➕ Add Entry", "📁 View Report", "🧾 Generate Invoice"])

# --- Dashboard ---
if tab == "📊 Dashboard":
    st.subheader("📈 Business Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Income", f"₹{income_df['Amount'].sum():,.2f}")
    col2.metric("💸 Total Expenses", f"₹{expense_df['Amount'].sum():,.2f}")
    net_profit = income_df['Amount'].sum() - expense_df['Amount'].sum()
    col3.metric("📊 Net Profit", f"₹{net_profit:,.2f}")

# --- Add Entry ---
elif tab == "➕ Add Entry":
    st.subheader("➕ Add Income or Expense")
    entry_type = st.radio("Entry Type", ["Income", "Expense"], horizontal=True)

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
            if entry_type == "Income":
                income_sheet.append_row([str(date), client, service, amount, notes])
            else:
                expense_sheet.append_row([str(date), category, "", amount, notes])
            st.success(f"{entry_type} entry added successfully!")

# --- View Report ---
elif tab == "📁 View Report":
    st.subheader("💰 Income Report")
    st.dataframe(income_df)
    st.download_button("⬇️ Download Income CSV", income_df.to_csv(index=False), file_name="income_report.csv")

    st.subheader("💸 Expense Report")
    st.dataframe(expense_df)
    st.download_button("⬇️ Download Expense CSV", expense_df.to_csv(index=False), file_name="expense_report.csv")

# --- Generate Invoice ---
elif tab == "🧾 Generate Invoice":
    st.subheader("🧾 Create Invoice")

    with st.form("invoice_form"):
        invoice_date = st.date_input("Invoice Date", datetime.date.today())
        client_input = st.text_input("Client Name (Type to search)")
        matching_clients = [c for c in existing_clients if client_input.lower() in c.lower()]
        client_name = st.selectbox("Select or Add Client", matching_clients + [client_input]) if client_input else ""
        service_type = st.text_input("Service Provided")
        amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
        notes = st.text_area("Notes (Optional)")
        submitted = st.form_submit_button("📤 Generate Invoice")

        if submitted:
            # Save invoice
            invoice_id = f"INV-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            income_sheet.append_row([str(invoice_date), client_name, service_type, amount, notes])

            # Save new customer
            if client_name not in existing_clients:
                new_customer_code = f"CUST-{len(existing_clients)+1:04d}"
                customer_sheet.append_row([new_customer_code, client_name])
                existing_clients.append(client_name)

            # Create HTML
            invoice_html = f"""
            <html><body>
            <h2 style='text-align:center;'>MytownERP - Invoice</h2>
            <p><b>Date:</b> {invoice_date}</p>
            <p><b>Client Name:</b> {client_name}</p>
            <p><b>Service:</b> {service_type}</p>
            <p><b>Amount:</b> ₹{amount:,.2f}</p>
            <p><b>Notes:</b> {notes or 'N/A'}</p>
            </body></html>
            """
            pdf_file = generate_pdf_from_html(invoice_html)

            if pdf_file:
                st.download_button(
                    label="📥 Download Invoice PDF",
                    data=pdf_file,
                    file_name=f"Invoice_{client_name}_{invoice_date}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("❌ PDF generation failed.")

            st.success("✅ Invoice created and income recorded.")
