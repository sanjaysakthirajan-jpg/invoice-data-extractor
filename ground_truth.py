GROUND_TRUTH = {
    "invoice_01_acme.txt": {
        "vendor_name": "Acme Robotics Supply Co.",
        "bill_to": "Northwind Manufacturing LLC",
        "invoice_number": "INV-2026-04471",
        "invoice_date": "2026-06-18",
        "due_date": "2026-07-18",
        "subtotal": 2511.00,
        "tax": 207.16,
        "total_due": 2718.16,
        "payment_terms": "Net 30",
        "line_item_count": 4,
    },
    "invoice_02_brightwave.txt": {
        "vendor_name": "Brightwave Consulting Group",
        "bill_to": "Meridian Health Partners",
        "invoice_number": "BW-8842",
        "invoice_date": "2026-05-02",
        "due_date": "2026-06-01",
        "subtotal": 7225.00,
        "tax": 0.00,
        "total_due": 7225.00,
        "payment_terms": "Net 30",
        "line_item_count": 3,
    },
    "invoice_03_riverside.txt": {
        "vendor_name": "Riverside Print & Signage",
        "bill_to": "Downtown Yoga Studio",
        "invoice_number": "7729",
        "invoice_date": "2026-03-14",
        "due_date": None,   # not stated in the source document
        "subtotal": None,   # not broken out separately in the source
        "tax": None,        # not mentioned in the source
        "total_due": 398.00,
        "payment_terms": None,  # not mentioned in the source
        "line_item_count": 3,
    },
}
