from flask import Blueprint, request, jsonify, session, current_app
import os, uuid, sys, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import save_invoice, get_invoices, get_db
from services.ocr_service import extract_text_from_file, parse_invoice_data
from routes.auth import login_required

invoices_bp = Blueprint("invoices", __name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "tiff", "pdf"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@invoices_bp.route("/upload-invoice", methods=["POST"])
@login_required
def upload_invoice():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file selected. Please choose a file to upload."}), 400

        file = request.files["file"]

        if not file or file.filename == "":
            return jsonify({"error": "No file selected."}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "File type not supported. Use JPG, PNG, or PDF."}), 400

        # Save file safely
        ext       = file.filename.rsplit(".", 1)[1].lower()
        safe_name = f"{uuid.uuid4().hex}.{ext}"
        upload_dir = os.path.join(current_app.root_path, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, safe_name)
        file.save(file_path)

        # OCR — never crashes, always returns text
        try:
            raw_text = extract_text_from_file(file_path)
        except Exception as e:
            print(f"[OCR] Error: {e}")
            raw_text = ""

        parsed = parse_invoice_data(raw_text)

        invoice_id = save_invoice(
            user_id       = session["user_id"],
            filename      = safe_name,
            file_path     = file_path,
            vendor_name   = parsed.get("vendor_name"),
            total_amount  = parsed.get("total_amount"),
            vat_amount    = parsed.get("vat_amount"),
            vendor_pan    = parsed.get("vendor_pan"),
            extracted_text= raw_text,
        )

        return jsonify({
            "message":    "Invoice uploaded successfully",
            "invoice_id": invoice_id,
            "extracted": {
                "vendor_name":  parsed.get("vendor_name"),
                "total_amount": parsed.get("total_amount"),
                "vat_amount":   parsed.get("vat_amount"),
                "vendor_pan":   parsed.get("vendor_pan"),
            }
        }), 201

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


@invoices_bp.route("/invoices", methods=["GET"])
@login_required
def list_invoices():
    try:
        rows = get_invoices(session["user_id"])
        return jsonify([dict(r) for r in rows]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoices_bp.route("/invoices/<int:invoice_id>/text", methods=["GET"])
@login_required
def get_invoice_text(invoice_id):
    inv = get_db().execute(
        "SELECT * FROM invoices WHERE id=? AND user_id=?",
        (invoice_id, session["user_id"])
    ).fetchone()
    if not inv:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"text": inv["extracted_text"]}), 200
