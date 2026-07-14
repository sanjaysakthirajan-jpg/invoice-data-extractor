import os
import sys
from pathlib import Path

import mysql.connector

from extract import extract_invoice, InvoiceData


def get_connection():
    return mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST", "localhost"),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        database=os.environ.get("MYSQL_DATABASE", "invoice_extraction"),
    )


def save_invoice(conn, source_file: str, data: InvoiceData) -> int:
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO invoices
            (source_file, vendor_name, bill_to, invoice_number, invoice_date,
             due_date, subtotal, tax, total_due, payment_terms)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            source_file,
            data.vendor_name,
            data.bill_to,
            data.invoice_number,
            data.invoice_date,
            data.due_date,
            data.subtotal,
            data.tax,
            data.total_due,
            data.payment_terms,
        ),
    )
    invoice_id = cursor.lastrowid

    for item in data.line_items:
        cursor.execute(
            """
            INSERT INTO line_items (invoice_id, description, quantity, unit_price, total)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (invoice_id, item.description, item.quantity, item.unit_price, item.total),
        )

    conn.commit()
    cursor.close()
    return invoice_id


def main(folder_path: str) -> None:
    folder = Path(folder_path)
    txt_files = sorted(folder.glob("*.txt"))

    if not txt_files:
        print(f"No .txt files found in {folder_path}")
        return

    conn = get_connection()

    for file_path in txt_files:
        print(f"Processing {file_path.name}...")
        try:
            text = file_path.read_text()
            data = extract_invoice(text)
            invoice_id = save_invoice(conn, file_path.name, data)
            print(f"  -> saved as invoice_id={invoice_id}, total_due=${data.total_due}")
        except Exception as e:
            print(f"  -> FAILED: {e}")

    conn.close()
    print("\nDone. Results stored in MySQL (invoice_extraction database)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python batch_extract_mysql.py <folder_of_txt_files>")
        sys.exit(1)

    main(sys.argv[1])