"""
Nepal Tax Engine
Calculates income tax, VAT, and provides audit summaries.
"""

from tax_config import TAX_CONFIG


def calculate_vat(amount: float, category: str = None) -> dict:
    """
    Given an amount that INCLUDES VAT (VAT-inclusive price),
    extract the VAT and base price.

    Nepal formula:
        VAT amount = Total × 13/113
        Base price  = Total - VAT
    """
    vat_exempt = TAX_CONFIG.get("vat_exempt_categories", [])
    if category and category in vat_exempt:
        return {"vat": 0.0, "base_price": amount, "vat_rate": 0.0, "vat_exempt": True}

    vat_rate = TAX_CONFIG["vat_rate"]
    vat = amount * vat_rate / (1 + vat_rate)
    base_price = amount - vat
    return {
        "vat": round(vat, 2),
        "base_price": round(base_price, 2),
        "vat_rate": vat_rate,
        "vat_exempt": False
    }


def calculate_income_tax(annual_salary: float) -> dict:
    """
    Calculate progressive income tax per Nepal's individual tax slabs.
    Returns breakdown by slab and total tax.
    """
    slabs = TAX_CONFIG["income_tax_slabs"]
    total_tax = 0.0
    slab_details = []
    remaining = annual_salary

    for slab in slabs:
        if remaining <= 0:
            break
        lower = slab["min"]
        upper = slab["max"]
        rate = slab["rate"]
        label = slab["label"]

        if upper is None:
            taxable = remaining
        else:
            slab_size = upper - lower
            taxable = min(remaining, slab_size)

        tax_in_slab = taxable * rate
        total_tax += tax_in_slab
        remaining -= taxable

        slab_details.append({
            "label": label,
            "taxable_amount": round(taxable, 2),
            "rate": rate,
            "rate_pct": f"{rate*100:.0f}%",
            "tax": round(tax_in_slab, 2),
        })

    return {
        "annual_salary": annual_salary,
        "total_income_tax": round(total_tax, 2),
        "monthly_income_tax": round(total_tax / 12, 2),
        "slab_details": slab_details,
    }


def calculate_effective_tax_rate(income_tax: float, vat_paid: float, annual_salary: float) -> dict:
    """
    Compute the combined (real) effective tax rate.
    """
    if annual_salary <= 0:
        return {"effective_rate": 0, "income_tax_rate": 0, "vat_rate_on_income": 0}

    total_tax = income_tax + vat_paid
    return {
        "total_tax_burden": round(total_tax, 2),
        "income_tax_rate": round(income_tax / annual_salary * 100, 2),
        "vat_rate_on_income": round(vat_paid / annual_salary * 100, 2),
        "effective_rate": round(total_tax / annual_salary * 100, 2),
    }


def generate_tax_audit(user, expenses_rows, year: int) -> dict:
    """
    Full audit summary for a given user and year.
    """
    annual_salary = user["salary"] or 0

    # Income tax
    income_tax_info = calculate_income_tax(annual_salary)

    # Aggregate VAT from expenses
    total_spent = sum(e["amount"] for e in expenses_rows)
    total_vat = sum(e["vat_amount"] for e in expenses_rows)
    total_base = sum(e["actual_price"] for e in expenses_rows)

    # Effective rate
    effective = calculate_effective_tax_rate(
        income_tax_info["total_income_tax"], total_vat, annual_salary
    )

    return {
        "year": year,
        "annual_salary": annual_salary,
        "income_tax": income_tax_info,
        "expenses": {
            "total_spent": round(total_spent, 2),
            "total_vat_paid": round(total_vat, 2),
            "total_base_price": round(total_base, 2),
            "transaction_count": len(expenses_rows),
        },
        "effective": effective,
        "summary": {
            "salary_tax": income_tax_info["total_income_tax"],
            "vat_paid": round(total_vat, 2),
            "total_tax_burden": round(income_tax_info["total_income_tax"] + total_vat, 2),
            "effective_rate_pct": effective["effective_rate"],
        }
    }


def estimate_refund(income_tax_paid: float, vat_paid: float) -> dict:
    """
    Rough refund estimation (illustrative — Nepal does not refund consumer VAT).
    Shows how much of consumer's money went to government.
    """
    total = income_tax_paid + vat_paid
    return {
        "income_tax_paid": round(income_tax_paid, 2),
        "vat_paid": round(vat_paid, 2),
        "total_to_government": round(total, 2),
        "note": (
            "Nepal does not currently offer VAT refunds for individual consumers. "
            "This report is for awareness and financial planning purposes."
        )
    }
