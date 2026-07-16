import sys
import json
from anthropic import Anthropic
from pydantic import BaseModel, Field
from typing import Optional

class LineItem(BaseModel):
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total: Optional[float] = None


class InvoiceData(BaseModel):
    vendor_name: str = Field(description="The company issuing the invoice")
    bill_to: str = Field(description="The company or person being billed")
    invoice_number: str
    invoice_date: str = Field(description="ISO format YYYY-MM-DD if possible")
    due_date: Optional[str] = Field(default=None, description="ISO format YYYY-MM-DD if possible")
    line_items: list[LineItem] = Field(default_factory=list)
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total_due: float
    payment_terms: Optional[str] = Field(
        default=None,
        description=(
            "Just the payment term itself, e.g. 'Net 30' or 'Due on receipt'. "
            "Do not include remittance/delivery instructions like 'wire transfer' "
            "or 'mail a check' -- those are a separate concern from the term."
        ),
    )


def pydantic_to_tool_schema(model: type[BaseModel], name: str, description: str) -> dict:

    schema = model.model_json_schema()

    return {
        "name": name,
        "description": description,
        "input_schema": schema,
    }



def extract_invoice(raw_text: str) -> InvoiceData:
    client = Anthropic()  # reads ANTHROPIC_API_KEY from environment

    tool = pydantic_to_tool_schema(
        InvoiceData,
        name="extract_invoice_data",
        description="Extract structured fields from an invoice document.",
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        tools=[tool],

        tool_choice={"type": "tool", "name": "extract_invoice_data"},
        messages=[
            {
                "role": "user",
                "content": f"Extract the invoice data from this document:\n\n{raw_text}",
            }
        ],
    )

    return _parse_tool_response(response)


def extract_invoice_from_pdf(pdf_bytes: bytes) -> InvoiceData:

    import base64

    client = Anthropic()

    tool = pydantic_to_tool_schema(
        InvoiceData,
        name="extract_invoice_data",
        description="Extract structured fields from an invoice document.",
    )

    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        tools=[tool],
        tool_choice={"type": "tool", "name": "extract_invoice_data"},
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Extract the invoice data from this document.",
                    },
                ],
            }
        ],
    )

    return _parse_tool_response(response)


def _parse_tool_response(response) -> InvoiceData:

    if response.stop_reason == "max_tokens":
        raise RuntimeError(
            "Extraction was cut off by the max_tokens limit -- the invoice is "
            "likely too large. Increase max_tokens and retry."
        )

    for block in response.content:
        if block.type == "tool_use":

            return InvoiceData.model_validate(block.input)

    raise RuntimeError("Model did not return a tool_use block")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extract.py <path_to_text_file>")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        text = f.read()

    result = extract_invoice(text)

    print(json.dumps(result.model_dump(), indent=2))
