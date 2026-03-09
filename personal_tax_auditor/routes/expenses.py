from flask import Blueprint, request, jsonify, session
import sys, os, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import (add_expense, get_expenses, delete_expense,
                    get_monthly_summary, get_category_summary)
from services.tax_engine import calculate_vat
from routes.auth import login_required
from tax_config import TAX_CONFIG

expenses_bp = Blueprint("expenses", __name__)


@expenses_bp.route("/add-expense", methods=["POST"])
@login_required
def add_expense_route():
    data = request.get_json()
    user_id = session["user_id"]

    date = data.get("date") or datetime.date.today().isoformat()
    vendor = (data.get("vendor") or "").strip()
    item = (data.get("item") or "").strip()
    category = data.get("category") or "Other"
    amount = float(data.get("amount") or 0)
    vat_included = int(data.get("vat_included", 1))
    notes = (data.get("notes") or "").strip()

    if not vendor or amount <= 0:
        return jsonify({"error": "Vendor and valid amount are required"}), 400

    if vat_included:
        vat_info = calculate_vat(amount, category)
        vat_amount = vat_info["vat"]
        actual_price = vat_info["base_price"]
    else:
        vat_amount = 0.0
        actual_price = amount

    add_expense(user_id, date, vendor, item, category, amount,
                vat_amount, actual_price, vat_included, notes)

    return jsonify({
        "message": "Expense added",
        "vat_amount": vat_amount,
        "actual_price": actual_price,
    }), 201


@expenses_bp.route("/expenses", methods=["GET"])
@login_required
def list_expenses():
    user_id = session["user_id"]
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    rows = get_expenses(user_id, year, month)
    return jsonify([dict(r) for r in rows]), 200


@expenses_bp.route("/expenses/<int:expense_id>", methods=["DELETE"])
@login_required
def remove_expense(expense_id):
    delete_expense(expense_id, session["user_id"])
    return jsonify({"message": "Deleted"}), 200


@expenses_bp.route("/monthly-summary", methods=["GET"])
@login_required
def monthly_summary():
    year = request.args.get("year", type=int, default=datetime.date.today().year)
    rows = get_monthly_summary(session["user_id"], year)

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    result = []
    data_map = {int(r["month"]): r for r in rows}
    for i in range(1, 13):
        r = data_map.get(i)
        result.append({
            "month": months[i-1],
            "month_num": i,
            "total_spent": r["total_spent"] if r else 0,
            "total_vat": r["total_vat"] if r else 0,
            "count": r["count"] if r else 0,
        })
    return jsonify(result), 200


@expenses_bp.route("/category-summary", methods=["GET"])
@login_required
def category_summary():
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    rows = get_category_summary(session["user_id"], year, month)
    return jsonify([dict(r) for r in rows]), 200


@expenses_bp.route("/categories", methods=["GET"])
def list_categories():
    return jsonify(TAX_CONFIG["expense_categories"]), 200
