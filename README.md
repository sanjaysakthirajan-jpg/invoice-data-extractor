# Invoice Data Extractor

A schema-driven document extraction pipeline that turns unstructured invoices (plain text or PDF) into clean, structured, queryable data using Claude's tool-calling API — no regex, no per-vendor templates, no OCR library.

## The problem

Businesses process large volumes of documents — invoices, receipts, purchase orders — that contain important structured information (vendor names, dates, line items, totals) but arrive as free-form text or PDFs. Traditionally this is solved one of two ways:

- **Manual data entry** — accurate but doesn't scale
- **Rule-based extraction (regex/templates)** — brittle; breaks the moment a vendor changes their invoice layout

This project uses an LLM instead: rather than writing parsing rules for every possible invoice format, you describe *what fields you want* as a schema, and the model reads the document and fills it in — including handling formats it's never seen before.

## How it works

1. **Schema definition** ([`extract.py`](extract.py)) — a `pydantic` model (`InvoiceData`) describes exactly which fields to extract (vendor, dates, line items, totals, etc.), including field-level descriptions that steer the model's behavior (e.g. "ISO format YYYY-MM-DD").
2. **Forced structured output** — the schema is converted into an Anthropic API "tool," and `tool_choice` forces Claude to respond by filling out that exact schema rather than replying with free text.
3. **Dual input support** — accepts either raw text or PDF bytes. PDFs are sent directly to Claude as a base64-encoded document; Claude reads the layout natively, no OCR step required.
4. **Validation** — every response is validated against the `pydantic` schema before use, catching any malformed output immediately.

```
Raw document (.txt or .pdf)
        │
        ▼
  extract.py  ──schema + tool_choice──▶  Claude API
        │                                     │
        │◀─────── structured JSON ───────────┘
        ▼
  Validated InvoiceData object
        │
        ├──▶ batch_extract_mysql.py  ──▶  MySQL (invoices + line_items)
        ├──▶ eval.py                 ──▶  Accuracy + consistency report
        └──▶ app.py (Streamlit)      ──▶  Web UI
```

## Features

- **Single or batch extraction** — process one file or an entire folder
- **Text and PDF input** — same schema, same code path, two document types
- **Relational storage** — results saved to MySQL with a proper `invoices` / `line_items` schema (one-to-many)
- **Evaluation harness** — measures extraction accuracy against manually verified ground truth, plus independent internal-consistency checks (does `quantity × unit_price ≈ total`? do line items sum to the subtotal?)
- **Web UI** — upload a document, see extracted data in a browser, no command line required

## Evaluation results

Ran against 3 invoices with deliberately different formats (structured table layout, prose-style consulting invoice, sparse print-shop invoice with missing fields):

```
=== invoice_01_acme.txt ===        10/10 fields correct
=== invoice_02_brightwave.txt ===  10/10 fields correct
=== invoice_03_riverside.txt ===   10/10 fields correct

OVERALL: 30/30 fields correct (100.0%)
```

**Note on getting here:** the first eval run scored 29/30 — Claude extracted `payment_terms` as `"Net 30 – wire transfer"` when the ground truth only expected `"Net 30"`. Investigating showed this wasn't an extraction error; the source document did contain both pieces of information, and the schema's field description hadn't specified that remittance instructions should be excluded. Tightening the field description in the schema resolved it on the next run. This is a realistic example of iterative prompt/schema engineering, not just a one-shot result.

Consistency checks (line-item math, subtotal reconciliation) also pass on all 3 documents.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key-here
```

For MySQL storage, also set:
```bash
export MYSQL_HOST=localhost
export MYSQL_USER=root
export MYSQL_PASSWORD=your-password
export MYSQL_DATABASE=invoice_extraction
```
and run `schema.sql` in MySQL Workbench first to create the database and tables.

## Usage

**Extract a single document:**
```bash
python extract.py sample_invoice.txt
```

**Batch process a folder into MySQL:**
```bash
python batch_extract.py invoices
```

**Run the evaluation suite:**
```bash
python eval.py invoices
```

**Launch the web UI:**
```bash
streamlit run app.py
```

## Project structure

```
structured-extraction/
├── extract.py                  # Core extraction logic (schema, API call, text + PDF)
├── batch_extract.py            # Batch processing into MySQL
├── schema.sql                  # MySQL table definitions
├── eval.py                     # Accuracy + consistency evaluation
├── ground_truth.py             # Manually verified correct answers for eval.py
├── app.py                      # Streamlit web UI
├── requirements.txt
├── .gitignore
└── invoices/                   # Sample invoices for testing (3 different formats)
```

## Known limitations

- No confidence scoring — the model returns a value or `null`, with no signal for "I'm unsure about this field"
- Eval set is small (3 documents); a production system would need dozens of documents across more format variations to trust accuracy numbers fully
- No handling yet for scanned/image-only PDFs (would need OCR as a fallback, since Claude reads text-based PDF content directly)
- Single-page documents only — untested on multi-page invoices

## Tech stack

Python · Anthropic API (Claude, tool use) · pydantic · MySQL · Streamlit
