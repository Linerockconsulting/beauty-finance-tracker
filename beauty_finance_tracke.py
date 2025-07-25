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
    st.markdown("## 🧾 Generate Invoice")

    # Show form first
    with st.form("invoice_form"):
        invoice_date = st.date_input("Invoice Date", datetime.date.today())

        client_name_input = st.text_input("Client Name", value="", placeholder="Start typing...")
        suggestions = [c for c in existing_clients if client_name_input.lower() in c.lower()]
        if suggestions:
            client_name = st.selectbox("Select Client", suggestions + [client_name_input], index=len(suggestions))
        else:
            client_name = client_name_input

        service_type = st.text_input("Service Provided")
        amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
        notes = st.text_area("Notes (Optional)")

        submitted = st.form_submit_button("📤 Generate Invoice")

    # If form was submitted, generate invoice
    if submitted:
        invoice_id = f"INV-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Save income entry
        row = [str(invoice_date), client_name, service_type, amount, notes]
        income_sheet.append_row(row)

        # Save customer if new
        if client_name not in existing_clients:
            new_customer_code = f"CUST-{len(existing_clients) + 1:04d}"
            customer_sheet.append_row([new_customer_code, client_name])
            existing_clients.append(client_name)

        st.success("✅ Invoice generated and saved!")

        # Prepare invoice HTML
        invoice_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ text-align: center; font-size: 24px; font-weight: bold; }}
                .invoice-box {{ margin: 20px; padding: 20px; border: 1px solid #eee; }}
                table {{ width: 100%; margin-top: 20px; }}
                th, td {{ padding: 8px; text-align: left; }}
            </style>
        </head>
        <body>
            <div class="invoice-box">
                <div class="header">MytownERP - Invoice</div>
                <p><strong>Invoice ID:</strong> {invoice_id}</p>
                <p><strong>Date:</strong> {invoice_date}</p>
                <p><strong>Client Name:</strong> {client_name}</p>
                <p><strong>Service:</strong> {service_type}</p>
                <p><strong>Amount:</strong> ₹{amount:,.2f}</p>
                <p><strong>Notes:</strong> {notes or "N/A"}</p>
            </div>
        </body>
        </html>
        """

        # Generate PDF
        pdf_file = generate_pdf_from_html(invoice_html)

        # Preview Invoice
        st.markdown(f"""
        ### 🧾 Invoice: {invoice_id}
        - **Date:** {invoice_date.strftime('%d-%m-%Y')}
        - **Client:** {client_name}
        - **Service:** {service_type}
        - **Amount:** ₹{amount:,.2f}
        - **Notes:** {notes or 'N/A'}

        ---
        **Thank you for your business!**
        """)

        # Show download button OUTSIDE form
        if pdf_file:
            st.download_button(
                label="📥 Download Invoice PDF",
                data=pdf_file,
                file_name=f"Invoice_{client_name}_{invoice_date}.pdf",
                mime="application/pdf"
            )
        else:
            st.error("❌ Failed to generate PDF. Please try again.")
