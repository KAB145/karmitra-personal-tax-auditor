from flask import Blueprint, request, jsonify, session, current_app, send_from_directory
import os, uuid, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import save_invoice, get_invoices
from services.ocr_service import extract_text_from_file, parse_invoice_data
from routes.auth import login_required

invoices_bp = Blueprint("invoices", __name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "tiff", "pdf"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@invoices_bp.route("/upload-invoice", methods=["POST"])
@login_required
def upload_invoice():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    safe_name = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = os.path.join(current_app.root_path, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, safe_name)
    file.save(file_path)

    # OCR extraction
    raw_text = extract_text_from_file(file_path)
    parsed = parse_invoice_data(raw_text)

    invoice_id = save_invoice(
        user_id=session["user_id"],
        filename=safe_name,
        file_path=file_path,
        vendor_name=parsed.get("vendor_name"),
        total_amount=parsed.get("total_amount"),
        vat_amount=parsed.get("vat_amount"),
        vendor_pan=parsed.get("vendor_pan"),
        extracted_text=raw_text,
    )

    return jsonify({
        "message": "Invoice uploaded",
        "invoice_id": invoice_id,
        "extracted": {
            "vendor_name": parsed.get("vendor_name"),
            "total_amount": parsed.get("total_amount"),
            "vat_amount": parsed.get("vat_amount"),
            "vendor_pan": parsed.get("vendor_pan"),
        }
    }), 201


@invoices_bp.route("/invoices", methods=["GET"])
@login_required
def list_invoices():
    rows = get_invoices(session["user_id"])
    return jsonify([dict(r) for r in rows]), 200


@invoices_bp.route("/invoices/<int:invoice_id>/text", methods=["GET"])
@login_required
def get_invoice_text(invoice_id):
    from models import get_db
    conn = get_db()
    inv = conn.execute(
        "SELECT * FROM invoices WHERE id=? AND user_id=?",
        (invoice_id, session["user_id"])
    ).fetchone()
    conn.close()
    if not inv:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"text": inv["extracted_text"]}), 200
