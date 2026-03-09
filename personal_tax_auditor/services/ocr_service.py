"""
OCR Service – extracts structured data from invoice images/PDFs.
Uses Tesseract when available; falls back to mock extraction.
"""

import re
import os

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


def extract_text_from_file(file_path: str) -> str:
    """Extract raw text from image or PDF."""
    ext = os.path.splitext(file_path)[1].lower()

    if not OCR_AVAILABLE:
        return _mock_extracted_text()

    if ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
        img = Image.open(file_path)
        return pytesseract.image_to_string(img, lang="eng+nep")

    elif ext == ".pdf":
        if not PDF_AVAILABLE:
            return "PDF OCR requires pdf2image. Please install it."
        pages = convert_from_path(file_path, dpi=200)
        texts = [pytesseract.image_to_string(p, lang="eng+nep") for p in pages]
        return "\n".join(texts)

    return ""


def parse_invoice_data(text: str) -> dict:
    """
    Parse extracted text to identify vendor, amounts, VAT, PAN.
    Uses heuristic regex patterns common on Nepali receipts.
    """
    result = {
        "vendor_name": None,
        "total_amount": None,
        "vat_amount": None,
        "vendor_pan": None,
        "raw_text": text,
    }

    if not text:
        return result

    lines = text.strip().split("\n")

    # Vendor name: usually first non-empty line
    for line in lines[:5]:
        stripped = line.strip()
        if len(stripped) > 3:
            result["vendor_name"] = stripped
            break

    # PAN number: 9-digit number after "PAN" or "VAT No"
    pan_match = re.search(r'(?:PAN|VAT\s*(?:No|Reg|Regd)?)[:\s#]*(\d{9})', text, re.IGNORECASE)
    if pan_match:
        result["vendor_pan"] = pan_match.group(1)

    # Total amount patterns
    total_patterns = [
        r'(?:Grand\s*Total|Total\s*Amount|TOTAL)[:\s]*(?:NPR|Rs\.?|NRs\.?)?[\s]*([\d,]+\.?\d*)',
        r'(?:Amount\s*Due|Net\s*Total)[:\s]*(?:NPR|Rs\.?)?[\s]*([\d,]+\.?\d*)',
        r'(?:NPR|Rs\.?|NRs\.?)\s*([\d,]+\.?\d{2})',
    ]
    for pattern in total_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                result["total_amount"] = float(m.group(1).replace(",", ""))
                break
            except ValueError:
                continue

    # VAT amount
    vat_patterns = [
        r'(?:VAT|Tax\s*@\s*13%?)[:\s]*(?:NPR|Rs\.?)?[\s]*([\d,]+\.?\d*)',
        r'(?:13%\s*VAT)[:\s]*([\d,]+\.?\d*)',
    ]
    for pattern in vat_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                result["vat_amount"] = float(m.group(1).replace(",", ""))
                break
            except ValueError:
                continue

    # Derive VAT if total found but VAT not explicitly listed
    if result["total_amount"] and not result["vat_amount"]:
        result["vat_amount"] = round(result["total_amount"] * 13 / 113, 2)

    return result


def _mock_extracted_text() -> str:
    """Return sample receipt text when Tesseract is unavailable (demo mode)."""
    return """
BHAT-BHATENI SUPERMARKET
PAN No: 302456789
Lazimpat, Kathmandu

Date: 2024-12-15

Item                    Qty    Rate    Amount
----------------------------------------------
Rice (5kg)              1      750     750.00
Cooking Oil 1L          2      280     560.00
Bread                   1      90       90.00
Vegetables              -      -       320.00
----------------------------------------------
Sub Total                              1720.00
VAT @ 13%                               198.23
----------------------------------------------
GRAND TOTAL                NPR        1918.23
----------------------------------------------
Thank you for shopping!
"""
