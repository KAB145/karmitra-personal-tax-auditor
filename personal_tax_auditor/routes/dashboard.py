from flask import Blueprint, request, jsonify, session
import sys, os, datetime, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import get_user_by_id, get_expenses, get_monthly_summary, get_category_summary
from services.tax_engine import (calculate_income_tax, generate_tax_audit,
                                  estimate_refund, calculate_vat)
from routes.auth import login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/get-dashboard", methods=["GET"])
@login_required
def get_dashboard():
    user_id = session["user_id"]
    year = request.args.get("year", type=int, default=datetime.date.today().year)
    month = request.args.get("month", type=int)

    user = get_user_by_id(user_id)
    expenses = get_expenses(user_id, year, month)
    monthly = get_monthly_summary(user_id, year)
    categories = get_category_summary(user_id, year, month)

    salary = user["salary"] or 0
    income_tax = calculate_income_tax(salary)

    total_spent = sum(e["amount"] for e in expenses)
    total_vat = sum(e["vat_amount"] for e in expenses)
    months_with_data = len([m for m in monthly if m["total_spent"] > 0]) or 1
    avg_monthly_spend = total_spent / 12 if not month else total_spent

    effective_rate = 0
    total_tax_burden = income_tax["total_income_tax"] + total_vat
    if salary > 0:
        effective_rate = round(total_tax_burden / salary * 100, 2)

    months_label = ["Jan","Feb","Mar","Apr","May","Jun",
                    "Jul","Aug","Sep","Oct","Nov","Dec"]
    monthly_chart = []
    data_map = {int(r["month"]): dict(r) for r in monthly}
    for i in range(1, 13):
        r = data_map.get(i, {})
        monthly_chart.append({
            "month": months_label[i-1],
            "spent": r.get("total_spent", 0) or 0,
            "vat": r.get("total_vat", 0) or 0,
        })

    return jsonify({
        "user": {
            "name": user["name"],
            "salary": salary,
            "employer": user["employer"],
        },
        "income_tax": income_tax,
        "expenses_summary": {
            "total_spent": round(total_spent, 2),
            "total_vat_paid": round(total_vat, 2),
            "avg_monthly_spend": round(avg_monthly_spend, 2),
            "transaction_count": len(expenses),
        },
        "tax_burden": {
            "income_tax": income_tax["total_income_tax"],
            "vat_paid": round(total_vat, 2),
            "total": round(total_tax_burden, 2),
            "effective_rate_pct": effective_rate,
        },
        "charts": {
            "monthly": monthly_chart,
            "categories": [dict(c) for c in categories],
        }
    }), 200


@dashboard_bp.route("/generate-tax-report", methods=["GET"])
@login_required
def generate_tax_report():
    user_id = session["user_id"]
    year = request.args.get("year", type=int, default=datetime.date.today().year)

    user = get_user_by_id(user_id)
    expenses = get_expenses(user_id, year)
    audit = generate_tax_audit(user, expenses, year)
    refund_est = estimate_refund(
        audit["income_tax"]["total_income_tax"],
        audit["expenses"]["total_vat_paid"]
    )

    category_rows = get_category_summary(user_id, year)
    audit["category_breakdown"] = [dict(r) for r in category_rows]
    audit["refund_estimation"] = refund_est
    audit["generated_at"] = datetime.datetime.now().isoformat()
    audit["user"] = {
        "name": user["name"],
        "pan_number": user["pan_number"],
        "employer": user["employer"],
    }

    return jsonify(audit), 200


@dashboard_bp.route("/vat-calculator", methods=["POST"])
def vat_calculator():
    data = request.get_json()
    amount = float(data.get("amount") or 0)
    category = data.get("category")
    result = calculate_vat(amount, category)
    return jsonify(result), 200
