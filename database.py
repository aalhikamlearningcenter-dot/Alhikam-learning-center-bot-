# ==========================================================
# ALHIKAM LEARNING CENTER V2
# DATABASE
#
# PAYMENT
# REGISTRATION
# TELEGRAM
# GOOGLE SHEETS
# REFERRAL
# COMMISSION
# WITHDRAWAL
# ==========================================================

import os
import sqlite3
import hashlib
import secrets
from datetime import datetime


# ==========================================================
# CONFIG
# ==========================================================

DATABASE_NAME = os.getenv(
    "DATABASE_NAME",
    "alhikam.db"
)


# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_connection():

    conn = sqlite3.connect(
        DATABASE_NAME,
        timeout=30,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    return conn


# ==========================================================
# HELPERS
# ==========================================================

def row_get(row, key, default=None):

    if row is None:
        return default

    try:

        if key in row.keys():

            value = row[key]

            if value is None:
                return default

            return value

    except Exception:
        pass

    try:

        return row.get(
            key,
            default
        )

    except Exception:

        return default


def hash_password(password):

    if password is None:
        password = ""

    return hashlib.sha256(
        str(password).encode("utf-8")
    ).hexdigest()


def verify_password(
    password,
    password_hash
):

    if not password_hash:
        return False

    return (
        hash_password(password)
        == password_hash
    )


def generate_withdrawal_code():

    return secrets.token_hex(4).upper()


# ==========================================================
# SAFE COLUMN MIGRATION
# ==========================================================

def add_column_if_missing(
    cursor,
    table,
    column,
    column_type
):

    columns = cursor.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    existing_columns = {
        row["name"]
        for row in columns
    }

    if column not in existing_columns:

        cursor.execute(
            f"""
            ALTER TABLE {table}
            ADD COLUMN {column}
            {column_type}
            """
        )

        print(
            f"Added database column: "
            f"{table}.{column}"
        )


# ==========================================================
# INITIALIZE DATABASE
# ==========================================================

def initialize_database():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        # ==================================================
        # PROMOTERS
        # ==================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS promoters (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                name TEXT NOT NULL,

                phone TEXT,

                email TEXT,

                referral_code TEXT UNIQUE NOT NULL,

                password_hash TEXT,

                withdrawal_code_hash TEXT,

                balance REAL DEFAULT 0,

                available_balance REAL DEFAULT 0,

                total_earned REAL DEFAULT 0,

                status TEXT DEFAULT 'active',

                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ==================================================
        # STUDENTS
        # ==================================================

        cursor.execute(
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

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(promoter_id)
                REFERENCES promoters(id)
            )
            """
        )

        # ==================================================
        # PAYMENTS
        # ==================================================

        cursor.execute(
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

                updated_at TEXT
            )
            """
        )

        # ==================================================
        # COMMISSIONS
        # ==================================================

        cursor.execute(
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

        # ==================================================
        # WITHDRAWALS
        # ==================================================

        cursor.execute(
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

        # ==================================================
        # STUDENT MIGRATIONS
        # ==================================================

        add_column_if_missing(
            cursor,
            "students",
            "payment_token",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "students",
            "telegram_username",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "students",
            "telegram_id",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "students",
            "telegram_name",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "students",
            "payment_plan",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "students",
            "amount_paid",
            "REAL DEFAULT 0"
        )

        add_column_if_missing(
            cursor,
            "students",
            "payment_status",
            "TEXT DEFAULT 'pending'"
        )

        add_column_if_missing(
            cursor,
            "students",
            "registration_completed",
            "INTEGER DEFAULT 0"
        )

        add_column_if_missing(
            cursor,
            "students",
            "referral_code",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "students",
            "promoter_id",
            "INTEGER"
        )

        # IMPORTANT:
        # THIS WAS MISSING BEFORE

        add_column_if_missing(
            cursor,
            "students",
            "faculty",
            "TEXT"
        )

        # ==================================================
        # PAYMENT MIGRATIONS
        # ==================================================

        add_column_if_missing(
            cursor,
            "payments",
            "transaction_id",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "payments",
            "amount",
            "REAL DEFAULT 0"
        )

        add_column_if_missing(
            cursor,
            "payments",
            "currency",
            "TEXT DEFAULT 'NGN'"
        )

        add_column_if_missing(
            cursor,
            "payments",
            "payment_plan",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "payments",
            "payment_status",
            "TEXT DEFAULT 'pending'"
        )

        add_column_if_missing(
            cursor,
            "payments",
            "referral_code",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "payments",
            "promoter_id",
            "INTEGER"
        )

        add_column_if_missing(
            cursor,
            "payments",
            "telegram_id",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "payments",
            "telegram_name",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "payments",
            "telegram_username",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "payments",
            "updated_at",
            "TEXT"
        )

        # ==================================================
        # PROMOTER MIGRATIONS
        # ==================================================

        add_column_if_missing(
            cursor,
            "promoters",
            "password_hash",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "promoters",
            "withdrawal_code_hash",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "promoters",
            "balance",
            "REAL DEFAULT 0"
        )

        add_column_if_missing(
            cursor,
            "promoters",
            "available_balance",
            "REAL DEFAULT 0"
        )

        add_column_if_missing(
            cursor,
            "promoters",
            "total_earned",
            "REAL DEFAULT 0"
        )

        add_column_if_missing(
            cursor,
            "promoters",
            "status",
            "TEXT DEFAULT 'active'"
        )

        # ==================================================
        # WITHDRAWAL MIGRATIONS
        # ==================================================

        add_column_if_missing(
            cursor,
            "withdrawals",
            "bank_name",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "withdrawals",
            "account_number",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "withdrawals",
            "account_name",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "withdrawals",
            "bank_code",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "withdrawals",
            "transfer_reference",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "withdrawals",
            "transfer_id",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "withdrawals",
            "status",
            "TEXT DEFAULT 'pending'"
        )

        add_column_if_missing(
            cursor,
            "withdrawals",
            "message",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "withdrawals",
            "updated_at",
            "TEXT"
        )

        # ==================================================
        # INDEXES
        # ==================================================

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_students_tx_ref

            ON students(tx_ref)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_students_telegram_id

            ON students(telegram_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_students_faculty

            ON students(faculty)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_payments_tx_ref

            ON payments(tx_ref)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_commissions_promoter

            ON commissions(promoter_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_withdrawals_promoter

            ON withdrawals(promoter_id)
            """
        )

        conn.commit()

        print(
            "Database initialized successfully."
        )

    except Exception as e:

        conn.rollback()

        print(
            "Database initialization error:",
            repr(e)
        )

        raise

    finally:

        conn.close()


# ==========================================================
# PROMOTERS
# ==========================================================

def add_promoter(
    name,
    phone,
    email,
    referral_code,
    password,
    withdrawal_code=None
):

    conn = get_connection()

    try:

        password_hash = hash_password(
            password
        )

        withdrawal_code_hash = None

        if withdrawal_code:

            withdrawal_code_hash = hash_password(
                withdrawal_code
            )

        cursor = conn.execute(
            """
            INSERT INTO promoters (
                name,
                phone,
                email,
                referral_code,
                password_hash,
                withdrawal_code_hash
            )

            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                phone,
                email,
                referral_code,
                password_hash,
                withdrawal_code_hash
            )
        )

        conn.commit()

        return cursor.lastrowid

    finally:

        conn.close()


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
                ).strip(),
            )
        ).fetchone()

    finally:

        conn.close()


# ==========================================================
# PAYMENTS
# ==========================================================

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

        else:

            conn.execute(
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

                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
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

        conn.commit()

        return True

    finally:

        conn.close()


def get_payment_by_tx_ref(
    tx_ref
):

    if not tx_ref:
        return None

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


def update_payment_status(
    tx_ref,
    status,
    transaction_id=None
):

    conn = get_connection()

    try:

        conn.execute(
            """
            UPDATE payments

            SET
                payment_status = ?,

                transaction_id =
                    COALESCE(
                        ?,
                        transaction_id
                    ),

                updated_at = ?

            WHERE tx_ref = ?
            """,
            (
                status,
                transaction_id,
                datetime.utcnow().isoformat(),
                tx_ref
            )
        )

        conn.commit()

        return True

    finally:

        conn.close()


# ==========================================================
# STUDENTS
# ==========================================================

def add_student(
    data_or_payment_token,
    tx_ref=None,
    full_name=None,
    phone=None,
    email=None,
    telegram_username=None,
    telegram_id=None,
    payment_plan=None,
    amount_paid=0,
    payment_status="pending",
    referral_code=None,
    promoter_id=None,
    faculty=None
):

    """
    Supports BOTH:

    add_student(database_data)

    and old positional style:

    add_student(
        payment_token,
        tx_ref,
        full_name,
        ...
    )
    """

    # ======================================================
    # DICTIONARY STYLE
    # ======================================================

    if isinstance(
        data_or_payment_token,
        dict
    ):

        data = data_or_payment_token

        payment_token = (
            data.get("payment_token")
            or data.get("tx_ref")
            or ""
        )

        tx_ref = (
            data.get("tx_ref")
            or tx_ref
            or ""
        )

        full_name = (
            data.get("full_name")
            or ""
        )

        phone = (
            data.get("phone")
            or ""
        )

        email = (
            data.get("email")
            or ""
        )

        telegram_username = (
            data.get(
                "telegram_username"
            )
            or data.get(
                "username"
            )
            or ""
        )

        telegram_id = (
            data.get(
                "telegram_id"
            )
            or ""
        )

        telegram_name = (
            data.get(
                "telegram_name"
            )
            or ""
        )

        payment_plan = (
            data.get(
                "payment_plan"
            )
            or ""
        )

        amount_paid = (
            data.get(
                "amount_paid"
            )
            or 0
        )

        payment_status = (
            data.get(
                "payment_status"
            )
            or "pending"
        )

        referral_code = (
            data.get(
                "referral_code"
            )
            or ""
        )

        promoter_id = (
            data.get(
                "promoter_id"
            )
        )

        # IMPORTANT:
        # registration.py uses faculty.
        # It also sends course=faculty.
        faculty = (
            data.get("faculty")
            or data.get("course")
            or ""
        )

    else:

        payment_token = (
            data_or_payment_token
            or ""
        )

        telegram_name = ""

    # ======================================================
    # CLEAN VALUES
    # ======================================================

    tx_ref = str(
        tx_ref or ""
    ).strip()

    faculty = str(
        faculty or ""
    ).strip()

    telegram_id = str(
        telegram_id or ""
    ).strip()

    telegram_username = str(
        telegram_username or ""
    ).strip()

    telegram_name = str(
        telegram_name or ""
    ).strip()

    if not tx_ref:

        raise ValueError(
            "Transaction reference is required."
        )

    # ======================================================
    # SAVE
    # ======================================================

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
                    referral_code = ?,
                    promoter_id = ?,
                    faculty = ?

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
                    float(
                        amount_paid or 0
                    ),
                    payment_status,
                    referral_code,
                    promoter_id,
                    faculty,
                    tx_ref
                )
            )

            conn.commit()

            print(
                "Student record updated:",
                tx_ref
            )

            return existing["id"]

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
                faculty
            )

            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?
            )
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
                float(
                    amount_paid or 0
                ),
                payment_status,
                1,
                referral_code,
                promoter_id,
                faculty
            )
        )

        conn.commit()

        return cursor.lastrowid

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ==========================================================
# GET STUDENT BY TX REF
# ==========================================================

def get_student_by_tx_ref(
    tx_ref
):

    if not tx_ref:
        return None

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


# ==========================================================
# GET STUDENT BY TELEGRAM ID
# ==========================================================

def get_student_by_telegram_id(
    telegram_id
):

    if telegram_id is None:
        return None

    telegram_id = str(
        telegram_id
    ).strip()

    if not telegram_id:
        return None

    conn = get_connection()

    try:

        return conn.execute(
            """
            SELECT *

            FROM students

            WHERE telegram_id = ?

            ORDER BY id DESC

            LIMIT 1
            """,
            (telegram_id,)
        ).fetchone()

    finally:

        conn.close()


# ==========================================================
# CREATE OR GET STUDENT
# ==========================================================

def create_or_get_student(
    payment_token,
    tx_ref,
    full_name,
    phone,
    email,
    telegram_username,
    telegram_id,
    payment_plan,
    amount_paid,
    payment_status,
    referral_code=None,
    promoter_id=None,
    faculty=None
):

    existing = get_student_by_tx_ref(
        tx_ref
    )

    if existing:

        add_student(
            {
                "payment_token":
                    payment_token,

                "tx_ref":
                    tx_ref,

                "full_name":
                    full_name,

                "phone":
                    phone,

                "email":
                    email,

                "telegram_username":
                    telegram_username,

                "telegram_id":
                    telegram_id,

                "payment_plan":
                    payment_plan,

                "amount_paid":
                    amount_paid,

                "payment_status":
                    payment_status,

                "referral_code":
                    referral_code,

                "promoter_id":
                    promoter_id,

                "faculty":
                    faculty
            }
        )

        return get_student_by_tx_ref(
            tx_ref
        )

    add_student(
        {
            "payment_token":
                payment_token,

            "tx_ref":
                tx_ref,

            "full_name":
                full_name,

            "phone":
                phone,

            "email":
                email,

            "telegram_username":
                telegram_username,

            "telegram_id":
                telegram_id,

            "payment_plan":
                payment_plan,

            "amount_paid":
                amount_paid,

            "payment_status":
                payment_status,

            "referral_code":
                referral_code,

            "promoter_id":
                promoter_id,

            "faculty":
                faculty
        }
    )

    return get_student_by_tx_ref(
        tx_ref
    )


# ==========================================================
# REGISTRATION STATUS
# ==========================================================

def mark_payment_registration_completed(
    tx_ref
):

    conn = get_connection()

    try:

        conn.execute(
            """
            UPDATE students

            SET registration_completed = 1

            WHERE tx_ref = ?
            """,
            (tx_ref,)
        )

        conn.commit()

        return True

    finally:

        conn.close()


def payment_registration_completed(
    tx_ref
):

    conn = get_connection()

    try:

        row = conn.execute(
            """
            SELECT registration_completed

            FROM students

            WHERE tx_ref = ?

            LIMIT 1
            """,
            (tx_ref,)
        ).fetchone()

        if not row:
            return False

        return int(
            row["registration_completed"]
            or 0
        ) == 1

    finally:

        conn.close()


# ==========================================================
# COMMISSION
# ==========================================================

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

    conn = get_connection()

    try:

        conn.execute(
            """
            INSERT INTO commissions (
                promoter_id,
                tx_ref,
                amount,
                status
            )

            VALUES (
                ?, ?, ?, 'available'
            )
            """,
            (
                promoter_id,
                tx_ref,
                amount
            )
        )

        conn.execute(
            """
            UPDATE promoters

            SET
                balance =
                    COALESCE(
                        balance,
                        0
                    ) + ?,

                available_balance =
                    COALESCE(
                        available_balance,
                        0
                    ) + ?,

                total_earned =
                    COALESCE(
                        total_earned,
                        0
                    ) + ?

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

        return True

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ==========================================================
# WITHDRAWAL
# ==========================================================

def create_withdrawal(
    promoter_id,
    amount,
    bank_name,
    account_number,
    account_name,
    bank_code,
    transfer_reference=None
):

    conn = get_connection()

    try:

        promoter = conn.execute(
            """
            SELECT available_balance

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

        available = float(
            promoter["available_balance"]
            or 0
        )

        amount = float(
            amount
        )

        if amount <= 0:

            raise ValueError(
                "Invalid withdrawal amount."
            )

        if amount > available:

            raise ValueError(
                "Insufficient available balance."
            )

        cursor = conn.execute(
            """
            INSERT INTO withdrawals (
                promoter_id,
                amount,
                bank_name,
                account_number,
                account_name,
                bank_code,
                transfer_reference,
                status
            )

            VALUES (
                ?, ?, ?, ?, ?, ?, ?, 'pending'
            )
            """,
            (
                promoter_id,
                amount,
                bank_name,
                account_number,
                account_name,
                bank_code,
                transfer_reference
            )
        )

        withdrawal_id = cursor.lastrowid

        conn.execute(
            """
            UPDATE promoters

            SET available_balance =
                available_balance - ?

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


# ==========================================================
# PROCESS TRANSFER RESULT
# ==========================================================

def process_transfer_result(
    withdrawal_id,
    flutterwave_status,
    transfer_id=None,
    transfer_reference=None,
    message=None
):

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

        old_status = (
            withdrawal["status"]
            or "pending"
        )

        new_status = str(
            flutterwave_status
            or "processing"
        ).strip().lower()

        # ==================================================
        # SUCCESSFUL
        # ==================================================

        if new_status in (
            "successful",
            "success",
            "completed"
        ):

            conn.execute(
                """
                UPDATE withdrawals

                SET
                    status = 'successful',

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

                    message = ?,

                    updated_at = ?

                WHERE id = ?
                """,
                (
                    transfer_id,
                    transfer_reference,
                    message,
                    datetime.utcnow().isoformat(),
                    withdrawal_id
                )
            )

            conn.commit()

            return True

        # ==================================================
        # FAILED / CANCELLED
        # ==================================================

        if new_status in (
            "failed",
            "cancelled",
            "canceled"
        ):

            if old_status not in (
                "failed",
                "cancelled",
                "canceled",
                "successful"
            ):

                conn.execute(
                    """
                    UPDATE promoters

                    SET available_balance =
                        COALESCE(
                            available_balance,
                            0
                        ) + ?

                    WHERE id = ?
                    """,
                    (
                        withdrawal["amount"],
                        withdrawal["promoter_id"]
                    )
                )

            conn.execute(
                """
                UPDATE withdrawals

                SET
                    status = ?,

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

                    message = ?,

                    updated_at = ?

                WHERE id = ?
                """,
                (
                    new_status,
                    transfer_id,
                    transfer_reference,
                    message,
                    datetime.utcnow().isoformat(),
                    withdrawal_id
                )
            )

            conn.commit()

            return True

        # ==================================================
        # PROCESSING / PENDING
        # ==================================================

        conn.execute(
            """
            UPDATE withdrawals

            SET
                status = ?,

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

                message = ?,

                updated_at = ?

            WHERE id = ?
            """,
            (
                new_status,
                transfer_id,
                transfer_reference,
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


# ==========================================================
# START DATABASE
# ==========================================================

initialize_database()