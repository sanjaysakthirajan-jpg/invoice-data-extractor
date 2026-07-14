CREATE DATABASE IF NOT EXISTS invoice_extraction;
USE invoice_extraction;

CREATE TABLE IF NOT EXISTS invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_file VARCHAR(255),
    vendor_name VARCHAR(255),
    bill_to VARCHAR(255),
    invoice_number VARCHAR(100),
    invoice_date VARCHAR(20),
    due_date VARCHAR(20),
    subtotal DECIMAL(12, 2),
    tax DECIMAL(12, 2),
    total_due DECIMAL(12, 2),
    payment_terms VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS line_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT,
    description VARCHAR(500),
    quantity DECIMAL(10, 2),
    unit_price DECIMAL(12, 2),
    total DECIMAL(12, 2),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
);
