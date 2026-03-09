# KarMitra – Personal Tax Auditor for Nepal

A FinTech web application that helps Nepali individuals understand their **real tax burden** — combining income tax (TDS) with VAT hidden in everyday purchases.

---

## Quick Start

```bash
# 1. Install dependencies
pip install flask

# Optional: OCR support
pip install pytesseract Pillow pdf2image

# 2. Run the app
cd personal_tax_auditor
python app.py
```

Visit: http://localhost:5000

---

## Project Structure

```
personal_tax_auditor/
├── app.py                  ← Flask entry point + page routes
├── models.py               ← SQLite database helpers
├── tax_config.py           ← Nepal tax rules (edit slabs here)
├── requirements.txt
│
├── routes/
│   ├── auth.py             ← /api/login, /api/register, /api/profile
│   ├── expenses.py         ← /api/add-expense, /api/expenses
│   ├── invoices.py         ← /api/upload-invoice, /api/invoices
│   └── dashboard.py        ← /api/get-dashboard, /api/generate-tax-report
│
├── services/
│   ├── tax_engine.py       ← Nepal income tax slabs + VAT calculation
│   └── ocr_service.py      ← Tesseract OCR + invoice parsing
│
├── templates/
│   ├── base.html           ← Sidebar layout
│   ├── landing.html        ← Homepage
│   ├── auth.html           ← Login / Register
│   ├── dashboard.html      ← Main dashboard with charts
│   ├── expenses.html       ← Expense tracker
│   ├── invoices.html       ← Invoice upload + OCR
│   ├── report.html         ← Annual tax report
│   └── profile.html        ← User profile + VAT calculator
│
└── static/
    ├── css/main.css
    └── js/app.js
```

---

## Nepal Tax Rules (FY 2080/81)

### VAT
- Standard rate: **13%** on all goods and services
- Formula: `VAT = Amount × 13 / 113`
- Exempt categories: Healthcare, Education

### Income Tax (Individual)
| Slab | Rate |
|------|------|
| Up to NPR 5,00,000 | 1% |
| NPR 5,00,001 – 7,00,000 | 10% |
| NPR 7,00,001 – 10,00,000 | 20% |
| Above NPR 10,00,000 | 30% |

To update tax slabs, edit `tax_config.py` — no code changes needed.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/register | Create account |
| POST | /api/login | Sign in |
| POST | /api/logout | Sign out |
| GET/PUT | /api/profile | Get/update profile |
| POST | /api/add-expense | Add expense (VAT auto-calculated) |
| GET | /api/expenses | List expenses (filter by year/month) |
| DELETE | /api/expenses/:id | Delete expense |
| GET | /api/monthly-summary | Monthly totals for charts |
| GET | /api/category-summary | Category breakdown |
| POST | /api/upload-invoice | Upload + OCR extract invoice |
| GET | /api/invoices | List invoices |
| GET | /api/get-dashboard | Full dashboard data |
| GET | /api/generate-tax-report | Annual tax audit |
| POST | /api/vat-calculator | Standalone VAT calculation |

---

## OCR Setup (Optional)

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-nep

# macOS
brew install tesseract

pip install pytesseract Pillow pdf2image
```

Without Tesseract, the app uses **demo mode** with a sample receipt.

---

## Security Notes

- Passwords are hashed with Werkzeug PBKDF2
- Session-based authentication
- File uploads are UUID-renamed to prevent path traversal
- Input validation on all API endpoints
- Change `SECRET_KEY` in production: `export SECRET_KEY=your-secret-key`

---

## Scaling to PostgreSQL

Replace SQLite in `models.py`:
```python
# Change DB_PATH to use psycopg2 or SQLAlchemy
DATABASE_URL = "postgresql://user:pass@localhost/karmitra"
```
