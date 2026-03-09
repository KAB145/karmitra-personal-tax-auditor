# Nepal Tax Configuration
# Update these values when tax rules change

TAX_CONFIG = {
    "vat_rate": 0.13,  # 13% VAT in Nepal

    # Income Tax Slabs (NPR) - FY 2080/81
    # Format: (upper_limit, rate)  None = no upper limit
    "income_tax_slabs": [
        {"min": 0,         "max": 500000,   "rate": 0.01,  "label": "Up to 5 Lakh"},
        {"min": 500001,    "max": 700000,   "rate": 0.10,  "label": "5L – 7L"},
        {"min": 700001,    "max": 1000000,  "rate": 0.20,  "label": "7L – 10L"},
        {"min": 1000001,   "max": None,     "rate": 0.30,  "label": "Above 10L"},
    ],

    # Expense Categories
    "expense_categories": [
        "Food & Dining",
        "Groceries",
        "Transport",
        "Utilities",
        "Healthcare",
        "Education",
        "Clothing",
        "Electronics",
        "Entertainment",
        "Household",
        "Personal Care",
        "Other",
    ],

    # VAT-exempt categories (no VAT applied)
    "vat_exempt_categories": [
        "Healthcare",
        "Education",
    ],

    "currency": "NPR",
    "fiscal_year_start_month": 7,  # Shrawan (July/August in Nepali calendar)
}
