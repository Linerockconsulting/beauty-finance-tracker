from xhtml2pdf import pisa
import io
import streamlit as st
import pandas as pd
import datetime
import gspread
import pdfkit
import tempfile
import datetime
from oauth2client.service_account import ServiceAccountCredentials

def generate_pdf_from_html(html: str):
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(html), dest=result)
    if pisa_status.err:
        return None
    return result.getvalue()

# 1️⃣ --- CONFIGS ---
st.set_page_config(page_title="B-Keepers Finance ERP", layout="wide")

# 2️⃣ --- AUTH ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
client = gspread.authorize(creds)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1zhx8YZ48h3qhRRaxk8pfntzNodJ0rjNWPKiWrNKfdk8/edit")
income_sheet = sheet.worksheet("Income")
expense_sheet = sheet.worksheet("Expenses")

# 3️⃣ --- FETCH DATA ---
customer_sheet = sheet.worksheet("Customers")

# Fetch customer data
customer_data = customer_sheet.get_all_values()[1:]  # Skip header
customer_df = pd.DataFrame(customer_data, columns=["Customer Code", "Client Name"])
existing_clients = customer_df["Client Name"].tolist()

income_data = income_sheet.get_all_values()[1:]  # Skip header
expense_data = expense_sheet.get_all_values()[1:]  # Skip header

income_df = pd.DataFrame(income_data, columns=["Date", "Client", "Service", "Amount", "Notes"])
expense_df = pd.DataFrame(expense_data, columns=["Date", "Category", "Amount", "Notes"])

income_df["Amount"] = pd.to_numeric(income_df["Amount"], errors="coerce").fillna(0)
expense_df["Amount"] = pd.to_numeric(expense_df["Amount"], errors="coerce").fillna(0)

# 4️⃣ --- PAGE NAVIGATION ---
st.title(" B-Keepers Finance ERP")
st.markdown("Effortlessly track your income and expenses for your beauty business 💼")
st.markdown("---")

tab = st.selectbox("📍 Select a page", ["📊 Dashboard", "➕ Add Entry", "📁 View Report","🧾 Generate Invoice"])


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
            if entry_type == "Income":
                row = [str(date), client, service, amount, notes]
                income_sheet.append_row(row)
            else:
                row = [str(date), category, "", amount, notes]
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

# 8️⃣ --- GENERATE INVOICE ---
elif tab == "🧾 Generate Invoice":
    st.markdown("## 🧾 Generate Invoice")

    with st.form("invoice_form"):
        invoice_date = st.date_input("Invoice Date", datetime.date.today())

        # Autocomplete customer name using selectbox logic
        client_name_input = st.text_input("Client Name", value="", placeholder="Start typing...")
        suggestions = [c for c in existing_clients if client_name_input.lower() in c.lower()]
        if suggestions:
            client_name = st.selectbox("Select Client", suggestions + [client_name_input], index=len(suggestions))
        else:
            client_name = client_name_input  # No suggestion, use raw input

        service_type = st.text_input("Service Provided")
        amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
        notes = st.text_area("Notes (Optional)")

        submitted = st.form_submit_button("📤 Generate Invoice")

        if submitted:
            # Generate unique invoice number
            invoice_id = f"INV-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
if submitted:
    # Save the invoice entry to Google Sheets
    row = [str(invoice_date), client_name, service_type, amount, notes]
    income_sheet.append_row(row)
    st.success("✅ Invoice generated and saved!")

    # Step 4: Create the Invoice HTML content
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
            <p><strong>Date:</strong> {invoice_date}</p>
            <p><strong>Client Name:</strong> {client_name}</p>
            <p><strong>Service:</strong> {service_type}</p>
            <p><strong>Amount:</strong> ₹{amount:,.2f}</p>
            <p><strong>Notes:</strong> {notes}</p>
        </div>
    </body>
    </html>
    """

    # Step 5: Generate the PDF from the HTML
    pdf_file = generate_pdf_from_html(invoice_html)

    if pdf_file:
        st.download_button(
            label="📥 Download Invoice PDF",
            data=pdf_file,
            file_name=f"Invoice_{client_name}_{invoice_date}.pdf",
            mime="application/pdf"
        )
    else:
        st.error("❌ Failed to generate PDF. Please try again.")
           

            # Show invoice preview
            invoice_md = f"""
            ### 🧾 Invoice: {invoice_id}
            - **Date:** {invoice_date.strftime('%d-%m-%Y')}
            - **Client:** {client_name}
            - **Service:** {service_type}
            - **Amount:** ₹{amount:,.2f}
            - **Notes:** {notes or 'N/A'}

            ---
            **Thank you for your business!**
            """
            st.markdown(invoice_md)

            # 1️⃣ Save invoice as income
            row = [str(invoice_date), client_name, service_type, amount, notes]
            income_sheet.append_row(row)

            # 2️⃣ Add client to customer master if not present
            if client_name not in existing_clients:
                new_customer_code = f"CUST-{len(existing_clients) + 1:04d}"
                customer_sheet.append_row([new_customer_code, client_name])
                existing_clients.append(client_name)  # Update local list

            st.success("✅ Invoice generated and income recorded.")

