import streamlit as st
import pandas as pd

from extract import extract_invoice, extract_invoice_from_pdf

st.set_page_config(page_title="Invoice Extractor", page_icon="🧾")

st.title("Invoice data extractor")
st.write(
    "Upload an invoice as a `.txt` or `.pdf` file. Claude will extract vendor info, "
    "dates, line items, and totals into structured data."
)

uploaded_file = st.file_uploader("Choose an invoice file", type=["txt", "pdf"])

if uploaded_file is not None:
    is_pdf = uploaded_file.name.lower().endswith(".pdf")

    if is_pdf:
        st.write("PDF uploaded -- Claude will read it directly.")
    else:
        raw_text = uploaded_file.read().decode("utf-8")
        with st.expander("View raw document text"):
            st.text(raw_text)

    with st.spinner("Extracting structured data..."):
        try:
            if is_pdf:
                data = extract_invoice_from_pdf(uploaded_file.read())
            else:
                data = extract_invoice(raw_text)
        except Exception as e:
            st.error(f"Extraction failed: {e}")
            st.stop()

    st.success("Extraction complete")

    # --- Summary fields ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Vendor", data.vendor_name)
    col2.metric("Invoice #", data.invoice_number)
    col3.metric("Total due", f"${data.total_due:,.2f}")

    st.subheader("Details")
    details = {
        "Bill to": data.bill_to,
        "Invoice date": data.invoice_date,
        "Due date": data.due_date or "Not specified",
        "Subtotal": f"${data.subtotal:,.2f}" if data.subtotal is not None else "Not specified",
        "Tax": f"${data.tax:,.2f}" if data.tax is not None else "Not specified",
        "Payment terms": data.payment_terms or "Not specified",
    }
    st.table(pd.DataFrame(details.items(), columns=["Field", "Value"]))

    # --- Line items table ---
    st.subheader("Line items")
    if data.line_items:
        rows = [
            {
                "Description": item.description,
                "Qty": item.quantity,
                "Unit price": item.unit_price,
                "Total": item.total,
            }
            for item in data.line_items
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.write("No line items extracted.")

    # --- Raw JSON, for the technically curious ---
    with st.expander("View raw JSON"):
        st.json(data.model_dump())