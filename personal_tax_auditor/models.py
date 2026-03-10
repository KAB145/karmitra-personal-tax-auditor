import sqlite3
import os
from flask import g

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")


def get_db():
    """
    Return a single shared connection per request (stored in Flask g).
    Falls back to a plain connection if called outside app context.
    Uses a 10-second timeout so SQLite waits instead of immediately
    raising "database is locked" on Windows.
    """
    try:
        if "db" not in g:
            g.db = sqlite3.connect(
                DB_PATH,
                timeout=10,           # wait up to 10s if locked
                check_same_thread=False,
            )
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA journal_mode=WAL")   # allows concurrent reads
            g.db.execute("PRAGMA foreign_keys = ON")
        return g.db
    except RuntimeError:
        # Outside app context (e.g. init_db called from CLI)
        conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


def close_db(e=None):
    """Close the connection at the end of each request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            pan_number TEXT,
            salary REAL DEFAULT 0,
            employer TEXT,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            vendor TEXT NOT NULL,
            item TEXT,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            vat_amount REAL DEFAULT 0,
            actual_price REAL DEFAULT 0,
            vat_included INTEGER DEFAULT 1,
            notes TEXT,
            invoice_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            vendor_name TEXT,
            total_amount REAL,
            vat_amount REAL,
            vendor_pan TEXT,
            extracted_text TEXT,
            upload_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS tax_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER,
            total_income REAL DEFAULT 0,
            income_tax_paid REAL DEFAULT 0,
            total_vat_paid REAL DEFAULT 0,
            total_expenses REAL DEFAULT 0,
            effective_tax_rate REAL DEFAULT 0,
            generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    print("Database initialized.")


# ── User helpers ──────────────────────────────────────────────────

def create_user(name, email, password_hash, pan_number=None, salary=0, employer=None):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (name, email, password_hash, pan_number, salary, employer) VALUES (?,?,?,?,?,?)",
            (name, email, password_hash, pan_number, salary, employer)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def get_user_by_email(email):
    return get_db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()


def get_user_by_id(user_id):
    return get_db().execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()


def update_user_profile(user_id, name, pan_number, salary, employer):
    conn = get_db()
    conn.execute(
        "UPDATE users SET name=?, pan_number=?, salary=?, employer=? WHERE id=?",
        (name, pan_number, salary, employer, user_id)
    )
    conn.commit()


# ── Expense helpers ───────────────────────────────────────────────

def add_expense(user_id, date, vendor, item, category, amount, vat_amount,
                actual_price, vat_included=1, notes=None, invoice_id=None):
    conn = get_db()
    conn.execute(
        """INSERT INTO expenses
           (user_id, date, vendor, item, category, amount, vat_amount,
            actual_price, vat_included, notes, invoice_id)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (user_id, date, vendor, item, category, amount, vat_amount,
         actual_price, vat_included, notes, invoice_id)
    )
    conn.commit()


def get_expenses(user_id, year=None, month=None):
    conn = get_db()
    if year and month:
        return conn.execute(
            "SELECT * FROM expenses WHERE user_id=? AND strftime('%Y-%m', date)=? ORDER BY date DESC",
            (user_id, f"{year}-{month:02d}")
        ).fetchall()
    elif year:
        return conn.execute(
            "SELECT * FROM expenses WHERE user_id=? AND strftime('%Y', date)=? ORDER BY date DESC",
            (user_id, str(year))
        ).fetchall()
    return conn.execute(
        "SELECT * FROM expenses WHERE user_id=? ORDER BY date DESC", (user_id,)
    ).fetchall()


def delete_expense(expense_id, user_id):
    conn = get_db()
    conn.execute("DELETE FROM expenses WHERE id=? AND user_id=?", (expense_id, user_id))
    conn.commit()


def get_monthly_summary(user_id, year):
    return get_db().execute(
        """SELECT strftime('%m', date) as month,
                  SUM(amount) as total_spent,
                  SUM(vat_amount) as total_vat,
                  COUNT(*) as count
           FROM expenses
           WHERE user_id=? AND strftime('%Y', date)=?
           GROUP BY strftime('%m', date)
           ORDER BY month""",
        (user_id, str(year))
    ).fetchall()


def get_category_summary(user_id, year=None, month=None):
    conn = get_db()
    if year and month:
        return conn.execute(
            """SELECT category, SUM(amount) as total, SUM(vat_amount) as vat
               FROM expenses WHERE user_id=? AND strftime('%Y-%m', date)=?
               GROUP BY category ORDER BY total DESC""",
            (user_id, f"{year}-{month:02d}")
        ).fetchall()
    elif year:
        return conn.execute(
            """SELECT category, SUM(amount) as total, SUM(vat_amount) as vat
               FROM expenses WHERE user_id=? AND strftime('%Y', date)=?
               GROUP BY category ORDER BY total DESC""",
            (user_id, str(year))
        ).fetchall()
    return conn.execute(
        """SELECT category, SUM(amount) as total, SUM(vat_amount) as vat
           FROM expenses WHERE user_id=? GROUP BY category ORDER BY total DESC""",
        (user_id,)
    ).fetchall()


# ── Invoice helpers ───────────────────────────────────────────────

def save_invoice(user_id, filename, file_path, vendor_name=None, total_amount=None,
                 vat_amount=None, vendor_pan=None, extracted_text=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO invoices
           (user_id, filename, file_path, vendor_name, total_amount,
            vat_amount, vendor_pan, extracted_text)
           VALUES (?,?,?,?,?,?,?,?)""",
        (user_id, filename, file_path, vendor_name, total_amount,
         vat_amount, vendor_pan, extracted_text)
    )
    conn.commit()
    return cursor.lastrowid


def get_invoices(user_id):
    return get_db().execute(
        "SELECT * FROM invoices WHERE user_id=? ORDER BY upload_date DESC", (user_id,)
    ).fetchall()
