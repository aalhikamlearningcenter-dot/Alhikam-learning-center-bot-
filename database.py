# ============================================================
# ALHIKAM LEARNING CENTER V2
# DATABASE
#
# Supports:
# - Students
# - Payments
# - Promoters
# - Referrals
# - Commissions
# - Withdrawals
# - Flutterwave Transfers
# - Admin Referral Dashboard
# - Promoter Dashboard
# - Secure Passwords
# - Secure Withdrawal Codes
# - Database Migrations
# ============================================================

import os
import sqlite3
import hashlib
import secrets

from datetime import datetime


# ============================================================
# CONFIG
# ============================================================

DATABASE_NAME = os.getenv(
    "DATABASE_NAME",
    "alhikam.db"
)

MINIMUM_WITHDRAWAL = 200


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    conn = sqlite3.connect(
        DATABASE_NAME,
        timeout=30
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


# ============================================================
# HELPERS
# ============================================================

def row_get(row, key, default=None):

    if row is None:
        return default

    try:

        if key in row.keys():

            value = row[key]

            if value is not None:
                return value

            return default

    except Exception:
        pass

    try:
        return row.get(
            key,
            default
        )
    except Exception:
        return default


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password):

    if password is None:
        raise ValueError(
            "Password is required."
        )

    password = str(password)

    if not password:
        raise ValueError(
            "Password cannot be empty."
        )

    salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120000
    ).hex()

    return f"pbkdf2_sha256$120000${salt}${password_hash}"


# ============================================================
# PASSWORD VERIFY
# ============================================================

def verify_password(
    password,
    stored_hash
):

    if not password:
        return False

    if not stored_hash:
        return False

    try:

        parts = stored_hash.split("$")

        if len(parts) != 4:
            return False

        algorithm = parts[0]
        iterations = int(parts[1])
        salt = parts[2]
        expected_hash = parts[3]

        if algorithm != "pbkdf2_sha256":
            return False

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            str(password).encode("utf-8"),
            salt.encode("utf-8"),
            iterations
        ).hex()

        return secrets.compare_digest(
            actual_hash,
            expected_hash
        )

    except Exception:
        return False


# ============================================================
# WITHDRAWAL CODE GENERATOR
# ============================================================

def generate_withdrawal_code():

    return secrets.token_hex(4).upper()


# ============================================================
# SAFE COLUMN MIGRATION
# ============================================================

def add_column_if_missing(
    conn,
    table_name,
    column_name,
    column_definition
):

    columns = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    existing = {
        row["name"]
        for row in columns
    }

    if column_name not in existing:

        conn.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name}
            {column_definition}
            """
        )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    conn = get_connection()

    try:

        # ====================================================
        # PROMOTERS
        # ====================================================

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS promoters (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                name TEXT NOT NULL,

                phone TEXT,

                email TEXT,

                referral_code TEXT UNIQUE NOT NULL,

                password_hash TEXT,

                withdrawal_code_hash TEXT,

                commission_rate REAL DEFAULT 10,

                balance REAL DEFAULT 0,

                available_balance REAL DEFAULT 0,

                total_earned REAL DEFAULT 0,

                total_sales REAL DEFAULT 0,

                withdrawn REAL DEFAULT 0,

                status TEXT DEFAULT 'active',

                created_at TEXT DEFAULT CURRENT_TIMESTAMP

            )
            """
        )

        # ====================================================
        # STUDENTS
        # ====================================================

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS students (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                payment_token TEXT,

                tx_ref TEXT UNIQUE NOT NULL,

                full_name TEXT,

                phone TEXT,

                email TEXT,

                telegram_username TEXT,

                telegram_id TEXT,

                telegram_name TEXT,

                payment_plan TEXT,

                amount_paid REAL DEFAULT 0,

                payment_status TEXT DEFAULT 'pending',

                registration_completed INTEGER DEFAULT 0,

                referral_code TEXT,

                promoter_id INTEGER,

                faculty TEXT,

                course TEXT,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(promoter_id)
                    REFERENCES promoters(id)

            )
            """
        )

        # ====================================================
        # PAYMENTS
        # ====================================================

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                tx_ref TEXT UNIQUE NOT NULL,

                transaction_id TEXT,

                amount REAL DEFAULT 0,

                currency TEXT DEFAULT 'NGN',

                payment_plan TEXT,

                payment_status TEXT DEFAULT 'pending',

                referral_code TEXT,

                promoter_id INTEGER,

                telegram_id TEXT,

                telegram_name TEXT,

                telegram_username TEXT,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT,

                FOREIGN KEY(promoter_id)
                    REFERENCES promoters(id)

            )
            """
        )

        # ====================================================
        # COMMISSIONS
        # ====================================================

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS commissions (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                promoter_id INTEGER NOT NULL,

                tx_ref TEXT NOT NULL,

                amount REAL DEFAULT 0,

                status TEXT DEFAULT 'available',

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(
                    promoter_id,
                    tx_ref
                ),

                FOREIGN KEY(promoter_id)
                    REFERENCES promoters(id)

            )
            """
        )

        # ====================================================
        # WITHDRAWALS
        # ====================================================

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS withdrawals (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                promoter_id INTEGER NOT NULL,

                amount REAL NOT NULL,

                bank_name TEXT,

                account_number TEXT,

                account_name TEXT,

                bank_code TEXT,

                transfer_reference TEXT,

                transfer_id TEXT,

                status TEXT DEFAULT 'pending',

                message TEXT,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT,

                FOREIGN KEY(promoter_id)
                    REFERENCES promoters(id)

            )
            """
        )

        # ====================================================
        # SAFE MIGRATIONS
        # ====================================================

        # Promoters
        add_column_if_missing(
            conn,
            "promoters",
            "commission_rate",
            "REAL DEFAULT 10"
        )

        add_column_if_missing(
            conn,
            "promoters",
            "total_sales",
            "REAL DEFAULT 0"
        )

        add_column_if_missing(
            conn,
            "promoters",
            "withdrawn",
            "REAL DEFAULT 0"
        )

        add_column_if_missing(
            conn,
            "promoters",
            "balance",
            "REAL DEFAULT 0"
        )

        add_column_if_missing(
            conn,
            "promoters",
            "available_balance",
            "REAL DEFAULT 0"
        )

        add_column_if_missing(
            conn,
            "promoters",
            "total_earned",
            "REAL DEFAULT 0"
        )

        add_column_if_missing(
            conn,
            "promoters",
            "status",
            "TEXT DEFAULT 'active'"
        )

        # Students
        add_column_if_missing(
            conn,
            "students",
            "faculty",
            "TEXT"
        )

        add_column_if_missing(
            conn,
            "students",
            "course",
            "TEXT"
        )

        add_column_if_missing(
            conn,
            "students",
            "referral_code",
            "TEXT"
        )

        add_column_if_missing(
            conn,
            "students",
            "promoter_id",
            "INTEGER"
        )

        # ====================================================
        # INDEXES
        # ====================================================

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_promoters_referral_code
            ON promoters(referral_code)
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_students_telegram_id
            ON students(telegram_id)
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_students_tx_ref
            ON students(tx_ref)
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_payments_tx_ref
            ON payments(tx_ref)
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_withdrawals_promoter
            ON withdrawals(promoter_id)
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_withdrawals_status
            ON withdrawals(status)
            """
        )

        conn.commit()

        print(
            "Database initialized successfully."
        )

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# PROMOTER
# ============================================================

def add_promoter(
    full_name,
    phone,
    email,
    commission_rate=10
):

    full_name = str(
        full_name or ""
    ).strip()

    phone = str(
        phone or ""
    ).strip()

    email = str(
        email or ""
    ).strip().lower()

    commission_rate = float(
        commission_rate or 10
    )

    if not full_name:
        raise ValueError(
            "Full name is required."
        )

    # --------------------------------------------------------
    # UNIQUE REFERRAL CODE
    # --------------------------------------------------------

    conn = get_connection()

    try:

        while True:

            referral_code = (
                "ALHIKAM-"
                + secrets.token_hex(5).upper()
            )

            exists = conn.execute(
                """
                SELECT id
                FROM promoters
                WHERE referral_code = ?
                LIMIT 1
                """,
                (referral_code,)
            ).fetchone()

            if not exists:
                break

        # ----------------------------------------------------
        # UNIQUE WITHDRAWAL CODE
        # ----------------------------------------------------

        while True:

            withdrawal_code = (
                generate_withdrawal_code()
            )

            withdrawal_hash = hash_password(
                withdrawal_code
            )

            # Hash collision is practically impossible,
            # but code generation remains independent.

            break

        # ----------------------------------------------------
        # INSERT
        # ----------------------------------------------------

        cursor = conn.execute(
            """
            INSERT INTO promoters (

                name,
                phone,
                email,
                referral_code,
                password_hash,
                withdrawal_code_hash,
                commission_rate,
                balance,
                available_balance,
                total_earned,
                total_sales,
                withdrawn,
                status

            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, 0, 'active')
            """,
            (
                full_name,
                phone,
                email,
                referral_code,
                None,
                withdrawal_hash,
                commission_rate
            )
        )

        promoter_id = cursor.lastrowid

        conn.commit()

        return {
            "id": promoter_id,
            "full_name": full_name,
            "referral_code": referral_code,
            "withdrawal_code": withdrawal_code,
            "commission_rate": commission_rate,
        }

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# SET PROMOTER PASSWORD
# ============================================================

def set_promoter_password(
    promoter_id,
    password
):

    if not promoter_id:
        return False

    if password is None:
        return False

    password = str(password)

    if not password:
        return False

    password_hash = hash_password(
        password
    )

    conn = get_connection()

    try:

        cursor = conn.execute(
            """
            UPDATE promoters
            SET password_hash = ?
            WHERE id = ?
            """,
            (
                password_hash,
                promoter_id
            )
        )

        conn.commit()

        return cursor.rowcount > 0

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# VERIFY PROMOTER PASSWORD
# ============================================================

def verify_promoter_password(
    promoter_id,
    password
):

    if not promoter_id:
        return False

    if password is None:
        return False

    conn = get_connection()

    try:

        promoter = conn.execute(
            """
            SELECT password_hash
            FROM promoters
            WHERE id = ?
            LIMIT 1
            """,
            (promoter_id,)
        ).fetchone()

        if not promoter:
            return False

        return verify_password(
            password,
            promoter["password_hash"]
        )

    finally:

        conn.close()


# ============================================================
# VERIFY WITHDRAWAL CODE
# ============================================================

def verify_promoter_withdrawal_code(
    promoter_id,
    withdrawal_code
):

    if not promoter_id:
        return False

    if withdrawal_code is None:
        return False

    conn = get_connection()

    try:

        promoter = conn.execute(
            """
            SELECT withdrawal_code_hash
            FROM promoters
            WHERE id = ?
            LIMIT 1
            """,
            (promoter_id,)
        ).fetchone()

        if not promoter:
            return False

        return verify_password(
            withdrawal_code,
            promoter["withdrawal_code_hash"]
        )

    finally:

        conn.close()


# ============================================================
# GET PROMOTER BY ID
# ============================================================

def get_promoter_by_id(
    promoter_id
):

    conn = get_connection()

    try:

        return conn.execute(
            """
            SELECT *
            FROM promoters
            WHERE id = ?
            LIMIT 1
            """,
            (promoter_id,)
        ).fetchone()

    finally:

        conn.close()


# ============================================================
# GET PROMOTER BY REFERRAL CODE
# ============================================================

def get_promoter_by_referral_code(
    referral_code
):

    if not referral_code:
        return None

    conn = get_connection()

    try:

        return conn.execute(
            """
            SELECT *
            FROM promoters
            WHERE referral_code = ?
            LIMIT 1
            """,
            (
                str(
                    referral_code
                ).strip()
            ,)
        ).fetchone()

    finally:

        conn.close()


# ============================================================
# GET ALL PROMOTERS
#
# Used by admin_referral.py
# ============================================================

def get_all_promoters():

    conn = get_connection()

    try:

        rows = conn.execute(
            """
            SELECT
                p.*,

                p.name AS full_name,

                COALESCE(
                    p.total_sales,
                    0
                ) AS total_sales,

                COALESCE(
                    p.available_balance,
                    0
                ) AS available_balance,

                COALESCE(
                    p.withdrawn,
                    0
                ) AS withdrawn,

                COALESCE(
                    p.commission_rate,
                    10
                ) AS commission_rate

            FROM promoters p

            ORDER BY p.id DESC
            """
        ).fetchall()

        return rows

    finally:

        conn.close()


# ============================================================
# SAVE PAYMENT
# ============================================================

def save_payment(
    tx_ref,
    transaction_id=None,
    amount=0,
    currency="NGN",
    payment_plan=None,
    payment_status="pending",
    referral_code=None,
    promoter_id=None,
    telegram_id=None,
    telegram_name=None,
    telegram_username=None
):

    conn = get_connection()

    try:

        existing = conn.execute(
            """
            SELECT id
            FROM payments
            WHERE tx_ref = ?
            LIMIT 1
            """,
            (tx_ref,)
        ).fetchone()

        now = datetime.utcnow().isoformat()

        if existing:

            conn.execute(
                """
                UPDATE payments

                SET
                    transaction_id = ?,
                    amount = ?,
                    currency = ?,
                    payment_plan = ?,
                    payment_status = ?,
                    referral_code = ?,
                    promoter_id = ?,
                    telegram_id = ?,
                    telegram_name = ?,
                    telegram_username = ?,
                    updated_at = ?

                WHERE tx_ref = ?
                """,
                (
                    transaction_id,
                    amount,
                    currency,
                    payment_plan,
                    payment_status,
                    referral_code,
                    promoter_id,
                    telegram_id,
                    telegram_name,
                    telegram_username,
                    now,
                    tx_ref
                )
            )

            payment_id = existing["id"]

        else:

            cursor = conn.execute(
                """
                INSERT INTO payments (

                    tx_ref,
                    transaction_id,
                    amount,
                    currency,
                    payment_plan,
                    payment_status,
                    referral_code,
                    promoter_id,
                    telegram_id,
                    telegram_name,
                    telegram_username,
                    updated_at

                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tx_ref,
                    transaction_id,
                    amount,
                    currency,
                    payment_plan,
                    payment_status,
                    referral_code,
                    promoter_id,
                    telegram_id,
                    telegram_name,
                    telegram_username,
                    now
                )
            )

            payment_id = cursor.lastrowid

        conn.commit()

        return payment_id

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# GET PAYMENT BY TX REF
# ============================================================

def get_payment_by_tx_ref(
    tx_ref
):

    conn = get_connection()

    try:

        return conn.execute(
            """
            SELECT *
            FROM payments
            WHERE tx_ref = ?
            LIMIT 1
            """,
            (tx_ref,)
        ).fetchone()

    finally:

        conn.close()


# ============================================================
# UPDATE PAYMENT STATUS
# ============================================================

def update_payment_status(
    tx_ref,
    status
):

    conn = get_connection()

    try:

        cursor = conn.execute(
            """
            UPDATE payments

            SET
                payment_status = ?,
                updated_at = ?

            WHERE tx_ref = ?
            """,
            (
                status,
                datetime.utcnow().isoformat(),
                tx_ref
            )
        )

        conn.commit()

        return cursor.rowcount > 0

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# ADD STUDENT
# ============================================================

def add_student(data, *args):

    # --------------------------------------------------------
    # DICT STYLE
    # --------------------------------------------------------

    if isinstance(data, dict):

        tx_ref = data.get(
            "tx_ref"
        ) or data.get(
            "payment_token"
        )

        payment_token = data.get(
            "payment_token"
        ) or tx_ref

        full_name = data.get(
            "full_name"
        )

        phone = data.get(
            "phone"
        )

        email = data.get(
            "email"
        )

        telegram_username = data.get(
            "telegram_username"
        )

        telegram_id = data.get(
            "telegram_id"
        )

        telegram_name = data.get(
            "telegram_name"
        )

        payment_plan = data.get(
            "payment_plan"
        )

        amount_paid = data.get(
            "amount_paid",
            0
        )

        payment_status = data.get(
            "payment_status",
            "pending"
        )

        registration_completed = data.get(
            "registration_completed",
            0
        )

        referral_code = data.get(
            "referral_code"
        )

        promoter_id = data.get(
            "promoter_id"
        )

        faculty = (
            data.get("faculty")
            or data.get("course")
            or ""
        )

        course = data.get(
            "course"
        ) or faculty

    # --------------------------------------------------------
    # OLD POSITIONAL STYLE
    # --------------------------------------------------------

    else:

        values = [
            data,
            *args
        ]

        values += [
            None
        ] * (
            14 - len(values)
        )

        (
            payment_token,
            tx_ref,
            full_name,
            phone,
            email,
            telegram_username,
            telegram_id,
            telegram_name,
            payment_plan,
            amount_paid,
            payment_status,
            registration_completed,
            referral_code,
            promoter_id
        ) = values[:14]

        faculty = ""
        course = ""

    if not tx_ref:

        raise ValueError(
            "tx_ref is required."
        )

    conn = get_connection()

    try:

        existing = conn.execute(
            """
            SELECT id
            FROM students
            WHERE tx_ref = ?
            LIMIT 1
            """,
            (tx_ref,)
        ).fetchone()

        if existing:

            conn.execute(
                """
                UPDATE students

                SET
                    payment_token = ?,
                    full_name = ?,
                    phone = ?,
                    email = ?,
                    telegram_username = ?,
                    telegram_id = ?,
                    telegram_name = ?,
                    payment_plan = ?,
                    amount_paid = ?,
                    payment_status = ?,
                    registration_completed = ?,
                    referral_code = ?,
                    promoter_id = ?,
                    faculty = ?,
                    course = ?

                WHERE tx_ref = ?
                """,
                (
                    payment_token,
                    full_name,
                    phone,
                    email,
                    telegram_username,
                    telegram_id,
                    telegram_name,
                    payment_plan,
                    amount_paid,
                    payment_status,
                    registration_completed,
                    referral_code,
                    promoter_id,
                    faculty,
                    course,
                    tx_ref
                )
            )

            student_id = existing["id"]

        else:

            cursor = conn.execute(
                """
                INSERT INTO students (

                    payment_token,
                    tx_ref,
                    full_name,
                    phone,
                    email,
                    telegram_username,
                    telegram_id,
                    telegram_name,
                    payment_plan,
                    amount_paid,
                    payment_status,
                    registration_completed,
                    referral_code,
                    promoter_id,
                    faculty,
                    course

                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payment_token,
                    tx_ref,
                    full_name,
                    phone,
                    email,
                    telegram_username,
                    telegram_id,
                    telegram_name,
                    payment_plan,
                    amount_paid,
                    payment_status,
                    registration_completed,
                    referral_code,
                    promoter_id,
                    faculty,
                    course
                )
            )

            student_id = cursor.lastrowid

        conn.commit()

        return student_id

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# GET STUDENT BY TX REF
# ============================================================

def get_student_by_tx_ref(
    tx_ref
):

    conn = get_connection()

    try:

        return conn.execute(
            """
            SELECT *
            FROM students
            WHERE tx_ref = ?
            LIMIT 1
            """,
            (tx_ref,)
        ).fetchone()

    finally:

        conn.close()


# ============================================================
# GET STUDENT BY TELEGRAM ID
# ============================================================

def get_student_by_telegram_id(
    telegram_id
):

    if telegram_id is None:
        return None

    conn = get_connection()

    try:

        return conn.execute(
            """
            SELECT *
            FROM students
            WHERE telegram_id = ?
            LIMIT 1
            """,
            (
                str(telegram_id)
            ,)
        ).fetchone()

    finally:

        conn.close()


# ============================================================
# CREATE OR GET STUDENT
# ============================================================

def create_or_get_student(
    data
):

    tx_ref = data.get(
        "tx_ref"
    )

    existing = get_student_by_tx_ref(
        tx_ref
    )

    if existing:
        return existing

    student_id = add_student(
        data
    )

    return get_student_by_tx_ref(
        tx_ref
    )


# ============================================================
# MARK REGISTRATION COMPLETED
# ============================================================

def mark_payment_registration_completed(
    tx_ref
):

    conn = get_connection()

    try:

        cursor = conn.execute(
            """
            UPDATE students

            SET
                registration_completed = 1,
                payment_status = 'Successful'

            WHERE tx_ref = ?
            """,
            (tx_ref,)
        )

        conn.commit()

        return cursor.rowcount > 0

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# CHECK REGISTRATION COMPLETED
# ============================================================

def payment_registration_completed(
    tx_ref
):

    student = get_student_by_tx_ref(
        tx_ref
    )

    if not student:
        return False

    return bool(
        row_get(
            student,
            "registration_completed",
            0
        )
    )


# ============================================================
# UPDATE STUDENT FACULTY
# ============================================================

def update_student_faculty(
    tx_ref,
    faculty
):

    conn = get_connection()

    try:

        cursor = conn.execute(
            """
            UPDATE students

            SET
                faculty = ?,
                course = ?

            WHERE tx_ref = ?
            """,
            (
                faculty,
                faculty,
                tx_ref
            )
        )

        conn.commit()

        return cursor.rowcount > 0

    finally:

        conn.close()


# ============================================================
# COMMISSION EXISTS
# ============================================================

def commission_exists(
    promoter_id,
    tx_ref
):

    conn = get_connection()

    try:

        row = conn.execute(
            """
            SELECT id
            FROM commissions
            WHERE promoter_id = ?
              AND tx_ref = ?
            LIMIT 1
            """,
            (
                promoter_id,
                tx_ref
            )
        ).fetchone()

        return row is not None

    finally:

        conn.close()


# ============================================================
# CREATE COMMISSION
# ============================================================

def create_commission(
    promoter_id,
    tx_ref,
    amount
):

    if commission_exists(
        promoter_id,
        tx_ref
    ):

        return False

    amount = float(
        amount or 0
    )

    if amount <= 0:
        return False

    conn = get_connection()

    try:

        cursor = conn.execute(
            """
            INSERT INTO commissions (

                promoter_id,
                tx_ref,
                amount,
                status

            )
            VALUES (?, ?, ?, 'available')
            """,
            (
                promoter_id,
                tx_ref,
                amount
            )
        )

        # ----------------------------------------------------
        # UPDATE PROMOTER BALANCES
        # ----------------------------------------------------

        conn.execute(
            """
            UPDATE promoters

            SET
                balance =
                    COALESCE(balance, 0)
                    + ?,

                available_balance =
                    COALESCE(available_balance, 0)
                    + ?,

                total_earned =
                    COALESCE(total_earned, 0)
                    + ?

            WHERE id = ?
            """,
            (
                amount,
                amount,
                amount,
                promoter_id
            )
        )

        conn.commit()

        return cursor.lastrowid

    except sqlite3.IntegrityError:

        conn.rollback()

        return False

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# CREATE WITHDRAWAL
# ============================================================

def create_withdrawal(
    promoter_id,
    amount,
    bank_name=None,
    account_number=None,
    account_name=None,
    bank_code=None
):

    amount = float(
        amount or 0
    )

    if amount <= 0:

        raise ValueError(
            "Withdrawal amount must be greater than zero."
        )

    if amount < MINIMUM_WITHDRAWAL:

        raise ValueError(
            f"Minimum withdrawal is ₦{MINIMUM_WITHDRAWAL:,.2f}."
        )

    conn = get_connection()

    try:

        promoter = conn.execute(
            """
            SELECT
                available_balance
            FROM promoters
            WHERE id = ?
            LIMIT 1
            """,
            (promoter_id,)
        ).fetchone()

        if not promoter:

            raise ValueError(
                "Promoter not found."
            )

        available_balance = float(
            promoter["available_balance"]
            or 0
        )

        if amount > available_balance:

            raise ValueError(
                "Insufficient available balance."
            )

        now = datetime.utcnow().isoformat()

        cursor = conn.execute(
            """
            INSERT INTO withdrawals (

                promoter_id,
                amount,
                bank_name,
                account_number,
                account_name,
                bank_code,
                status,
                created_at,
                updated_at

            )
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
            """,
            (
                promoter_id,
                amount,
                bank_name,
                account_number,
                account_name,
                bank_code,
                now,
                now
            )
        )

        withdrawal_id = cursor.lastrowid

        # ----------------------------------------------------
        # RESERVE BALANCE
        # ----------------------------------------------------

        conn.execute(
            """
            UPDATE promoters

            SET
                available_balance =
                    COALESCE(available_balance, 0)
                    - ?

            WHERE id = ?
            """,
            (
                amount,
                promoter_id
            )
        )

        conn.commit()

        return withdrawal_id

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# GET WITHDRAWAL BY ID
# ============================================================

def get_withdrawal_by_id(
    withdrawal_id
):

    conn = get_connection()

    try:

        return conn.execute(
            """
            SELECT *
            FROM withdrawals
            WHERE id = ?
            LIMIT 1
            """,
            (withdrawal_id,)
        ).fetchone()

    finally:

        conn.close()


# ============================================================
# GET PROMOTER WITHDRAWALS
# ============================================================

def get_withdrawals_by_promoter(
    promoter_id
):

    conn = get_connection()

    try:

        return conn.execute(
            """
            SELECT *
            FROM withdrawals

            WHERE promoter_id = ?

            ORDER BY id DESC
            """,
            (promoter_id,)
        ).fetchall()

    finally:

        conn.close()


# ============================================================
# COMPATIBILITY ALIAS
# ============================================================

def get_promoter_withdrawals(
    promoter_id
):

    return get_withdrawals_by_promoter(
        promoter_id
    )


# ============================================================
# GET ALL WITHDRAWALS
#
# Used by admin_referral.py
# ============================================================

def get_all_withdrawals():

    conn = get_connection()

    try:

        return conn.execute(
            """
            SELECT

                w.*,

                p.name AS promoter_name,

                p.email AS promoter_email,

                p.phone AS promoter_phone,

                p.referral_code AS promoter_referral_code

            FROM withdrawals w

            LEFT JOIN promoters p
                ON p.id = w.promoter_id

            ORDER BY w.id DESC
            """
        ).fetchall()

    finally:

        conn.close()


# ============================================================
# UPDATE WITHDRAWAL STATUS
#
# Used by admin_referral.py
# ============================================================

def update_withdrawal_status(
    withdrawal_id,
    status,
    message=None
):

    if not withdrawal_id:
        return False

    status = str(
        status or "pending"
    ).strip().lower()

    conn = get_connection()

    try:

        withdrawal = conn.execute(
            """
            SELECT *
            FROM withdrawals
            WHERE id = ?
            LIMIT 1
            """,
            (withdrawal_id,)
        ).fetchone()

        if not withdrawal:
            return False

        old_status = str(
            withdrawal["status"]
            or "pending"
        ).lower()

        # ----------------------------------------------------
        # DO NOT RESTORE TWICE
        # ----------------------------------------------------

        failed_statuses = {
            "failed",
            "cancelled",
            "canceled"
        }

        successful_statuses = {
            "successful",
            "success",
            "completed"
        }

        if (
            status in failed_statuses
            and old_status not in failed_statuses
        ):

            conn.execute(
                """
                UPDATE promoters

                SET
                    available_balance =
                        COALESCE(
                            available_balance,
                            0
                        )
                        + ?

                WHERE id = ?
                """,
                (
                    withdrawal["amount"],
                    withdrawal["promoter_id"]
                )
            )

        # ----------------------------------------------------
        # WITHDRAWAL STATUS
        # ----------------------------------------------------

        conn.execute(
            """
            UPDATE withdrawals

            SET
                status = ?,
                message = COALESCE(?, message),
                updated_at = ?

            WHERE id = ?
            """,
            (
                status,
                message,
                datetime.utcnow().isoformat(),
                withdrawal_id
            )
        )

        # ----------------------------------------------------
        # SUCCESSFUL WITHDRAWAL
        # ----------------------------------------------------

        if (
            status in successful_statuses
            and old_status not in successful_statuses
        ):

            conn.execute(
                """
                UPDATE promoters

                SET
                    withdrawn =
                        COALESCE(
                            withdrawn,
                            0
                        )
                        + ?

                WHERE id = ?
                """,
                (
                    withdrawal["amount"],
                    withdrawal["promoter_id"]
                )
            )

        conn.commit()

        return True

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# UPDATE WITHDRAWAL TRANSFER
# ============================================================

def update_withdrawal_transfer(
    withdrawal_id,
    transfer_id=None,
    transfer_reference=None,
    status=None,
    message=None
):

    if not withdrawal_id:
        return False

    conn = get_connection()

    try:

        withdrawal = conn.execute(
            """
            SELECT *
            FROM withdrawals
            WHERE id = ?
            LIMIT 1
            """,
            (withdrawal_id,)
        ).fetchone()

        if not withdrawal:
            return False

        current_status = (
            withdrawal["status"]
            or "pending"
        )

        new_status = (
            str(status).strip().lower()
            if status
            else current_status
        )

        conn.execute(
            """
            UPDATE withdrawals

            SET
                transfer_id =
                    COALESCE(
                        ?,
                        transfer_id
                    ),

                transfer_reference =
                    COALESCE(
                        ?,
                        transfer_reference
                    ),

                status = ?,

                message =
                    COALESCE(
                        ?,
                        message
                    ),

                updated_at = ?

            WHERE id = ?
            """,
            (
                transfer_id,
                transfer_reference,
                new_status,
                message,
                datetime.utcnow().isoformat(),
                withdrawal_id
            )
        )

        conn.commit()

        return True

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# PROCESS FLUTTERWAVE TRANSFER RESULT
# ============================================================

def process_transfer_result(
    withdrawal_id,
    flutterwave_status,
    transfer_id=None,
    transfer_reference=None,
    message=None
):

    status = str(
        flutterwave_status
        or "processing"
    ).strip().lower()

    successful = {
        "successful",
        "success",
        "completed"
    }

    failed = {
        "failed",
        "cancelled",
        "canceled"
    }

    if status in successful:

        final_status = "successful"

    elif status in failed:

        final_status = (
            "cancelled"
            if status in {
                "cancelled",
                "canceled"
            }
            else "failed"
        )

    else:

        final_status = status

    conn = get_connection()

    try:

        withdrawal = conn.execute(
            """
            SELECT *
            FROM withdrawals
            WHERE id = ?
            LIMIT 1
            """,
            (withdrawal_id,)
        ).fetchone()

        if not withdrawal:
            return False

        old_status = str(
            withdrawal["status"]
            or "pending"
        ).lower()

        # ----------------------------------------------------
        # FAILED / CANCELLED
        # ----------------------------------------------------

        if (
            final_status
            in {
                "failed",
                "cancelled"
            }
            and old_status
            not in {
                "failed",
                "cancelled"
            }
        ):

            conn.execute(
                """
                UPDATE promoters

                SET
                    available_balance =
                        COALESCE(
                            available_balance,
                            0
                        )
                        + ?

                WHERE id = ?
                """,
                (
                    withdrawal["amount"],
                    withdrawal["promoter_id"]
                )
            )

        # ----------------------------------------------------
        # SUCCESSFUL
        # ----------------------------------------------------

        if (
            final_status == "successful"
            and old_status
            not in {
                "successful",
                "success",
                "completed"
            }
        ):

            conn.execute(
                """
                UPDATE promoters

                SET
                    withdrawn =
                        COALESCE(
                            withdrawn,
                            0
                        )
                        + ?

                WHERE id = ?
                """,
                (
                    withdrawal["amount"],
                    withdrawal["promoter_id"]
                )
            )

        # ----------------------------------------------------
        # UPDATE WITHDRAWAL
        # ----------------------------------------------------

        conn.execute(
            """
            UPDATE withdrawals

            SET
                transfer_id =
                    COALESCE(
                        ?,
                        transfer_id
                    ),

                transfer_reference =
                    COALESCE(
                        ?,
                        transfer_reference
                    ),

                status = ?,

                message =
                    COALESCE(
                        ?,
                        message
                    ),

                updated_at = ?

            WHERE id = ?
            """,
            (
                transfer_id,
                transfer_reference,
                final_status,
                message,
                datetime.utcnow().isoformat(),
                withdrawal_id
            )
        )

        conn.commit()

        return True

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# INITIALIZE DATABASE
# ============================================================

initialize_database()