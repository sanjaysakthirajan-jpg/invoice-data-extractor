import sys
from pathlib import Path

from extract import extract_invoice, InvoiceData
from ground_truth import GROUND_TRUTH

TOLERANCE = 0.01  # allowable floating-point rounding difference for money


def fields_match(expected, actual) -> bool:
    if expected is None or actual is None:
        return expected == actual
    if isinstance(expected, float) or isinstance(actual, float):
        try:
            return abs(float(expected) - float(actual)) < TOLERANCE
        except (TypeError, ValueError):
            return False
    # Case-insensitive, whitespace-trimmed string comparison
    return str(expected).strip().lower() == str(actual).strip().lower()


def check_accuracy(filename: str, data: InvoiceData) -> tuple[int, int, list[str]]:
    """Compare extracted data against ground truth. Returns (correct, total, mismatches)."""
    truth = GROUND_TRUTH.get(filename)
    if truth is None:
        return 0, 0, [f"No ground truth defined for {filename}"]

    mismatches = []
    correct = 0
    total = 0

    for field in ["vendor_name", "bill_to", "invoice_number", "invoice_date",
                  "due_date", "subtotal", "tax", "total_due", "payment_terms"]:
        total += 1
        expected = truth[field]
        actual = getattr(data, field)
        if fields_match(expected, actual):
            correct += 1
        else:
            mismatches.append(f"  {field}: expected {expected!r}, got {actual!r}")

    total += 1
    if len(data.line_items) == truth["line_item_count"]:
        correct += 1
    else:
        mismatches.append(
            f"  line_item_count: expected {truth['line_item_count']}, got {len(data.line_items)}"
        )

    return correct, total, mismatches


def check_consistency(data: InvoiceData) -> list[str]:
    """Sanity checks independent of ground truth -- do the numbers add up?"""
    issues = []

    for item in data.line_items:
        if item.quantity is not None and item.unit_price is not None and item.total is not None:
            expected_total = item.quantity * item.unit_price
            if abs(expected_total - item.total) > TOLERANCE:
                issues.append(
                    f"  Line item '{item.description}': "
                    f"{item.quantity} x {item.unit_price} = {expected_total:.2f}, "
                    f"but total is listed as {item.total}"
                )

    line_items_sum = sum(item.total for item in data.line_items if item.total is not None)
    reference = data.subtotal if data.subtotal is not None else data.total_due
    if reference is not None and abs(line_items_sum - reference) > TOLERANCE:
        issues.append(
            f"  Line items sum to {line_items_sum:.2f}, but subtotal/total is {reference}"
        )

    return issues


def main(folder_path: str) -> None:
    folder = Path(folder_path)
    txt_files = sorted(folder.glob("*.txt"))

    total_correct = 0
    total_fields = 0

    for file_path in txt_files:
        print(f"\n=== {file_path.name} ===")
        text = file_path.read_text()
        data = extract_invoice(text)

        correct, total, mismatches = check_accuracy(file_path.name, data)
        total_correct += correct
        total_fields += total
        print(f"Accuracy: {correct}/{total} fields correct")
        for m in mismatches:
            print(m)

        issues = check_consistency(data)
        if issues:
            print("Consistency issues:")
            for i in issues:
                print(i)
        else:
            print("Consistency: OK (numbers add up)")

    print(f"\n=== OVERALL: {total_correct}/{total_fields} fields correct "
          f"({100 * total_correct / total_fields:.1f}%) ===")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python eval.py <folder_of_txt_files>")
        sys.exit(1)

    main(sys.argv[1])