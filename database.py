# ==========================================================
# ALHIKAM LEARNING CENTER V2
# database.py
#
# PAYMENT
# REFERRAL
# COMMISSION
# REGISTRATION
# WITHDRAWAL
# FLUTTERWAVE TRANSFER SUPPORT
#
# SECURE VERSION
# MINIMUM WITHDRAWAL = ₦200
#
# PROMOTER PASSWORD + WITHDRAWAL CODE SECURITY
# ==========================================================

import sqlite3
import logging
import secrets

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime, timezone

from werkzeug.security import generate_password_hash, check_password_hash

from config import DATABASE_NAME


logger = logging.getLogger(__name__)

MINIMUM_WITHDRAWAL = Decimal("200.00")

WITHDRAWAL_STATUSES = {
    "pending",
    "processing",
    "successful",
    "failed",
    "cancelled",
}


# ==========================================================
# TIME
# ==========================================================

def utc_now():
    return datetime.now(timezone.utc).isoformat()


# ==========================================================
# MONEY
# ==========================================================

def money(value):
    """
    Safely convert a value to Decimal with 2 decimal places.
    """

    try:

        amount = Decimal(str(value))

        if not amount.is_finite():
            raise ValueError(
                "Invalid money amount."
            )

        return amount.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

    except (
        InvalidOperation,
        ValueError,
        TypeError
    ):

        raise ValueError(
            "Invalid money amount."
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

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    conn.execute(
        "PRAGMA busy_timeout = 30000"
    )

    return conn


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

def initialize_database():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        # ==================================================
        # PROMOTERS
        # ==================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS promoters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                full_name TEXT NOT NULL,

                phone TEXT,

                email TEXT,

                referral_code TEXT NOT NULL UNIQUE,

                password_hash TEXT,

                withdrawal_code_hash TEXT,

                commission_rate REAL NOT NULL DEFAULT 0,

                total_sales REAL NOT NULL DEFAULT 0,

                total_earned REAL NOT NULL DEFAULT 0,

                available_balance REAL NOT NULL DEFAULT 0,

                withdrawn_amount REAL NOT NULL DEFAULT 0,

                status TEXT NOT NULL DEFAULT 'active',

                created_at TEXT NOT NULL
            )
        """)

        # ==================================================
        # STUDENTS
        # ==================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                payment_token TEXT,

                tx_ref TEXT UNIQUE,

                full_name TEXT,

                phone TEXT,

                email TEXT,

                telegram_username TEXT,

                telegram_id TEXT,

                payment_plan TEXT,

                amount_paid REAL NOT NULL DEFAULT 0,

                payment_status TEXT NOT NULL DEFAULT 'pending',

                registration_completed INTEGER NOT NULL DEFAULT 0,

                referral_code TEXT,

                promoter_id INTEGER,

                created_at TEXT NOT NULL,

                FOREIGN KEY(promoter_id)
                    REFERENCES promoters(id)
                    ON DELETE SET NULL
            )
        """)

        # ==================================================
        # PAYMENTS
        # ==================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                tx_ref TEXT NOT NULL UNIQUE,

                transaction_id TEXT,

                payment_plan TEXT,

                amount REAL NOT NULL DEFAULT 0,

                status TEXT NOT NULL DEFAULT 'pending',

                referral_code TEXT,

                promoter_id INTEGER,

                commission REAL NOT NULL DEFAULT 0,

                telegram_username TEXT,

                telegram_id TEXT,

                registration_completed INTEGER NOT NULL DEFAULT 0,

                created_at TEXT NOT NULL,

                FOREIGN KEY(promoter_id)
                    REFERENCES promoters(id)
                    ON DELETE SET NULL
            )
        """)

        # ==================================================
        # COMMISSIONS
        # ==================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS commissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                tx_ref TEXT NOT NULL UNIQUE,

                promoter_id INTEGER,

                student_id INTEGER,

                payment_amount REAL NOT NULL DEFAULT 0,

                commission_rate REAL NOT NULL DEFAULT 0,

                commission_amount REAL NOT NULL DEFAULT 0,

                status TEXT NOT NULL DEFAULT 'pending',

                created_at TEXT NOT NULL,

                FOREIGN KEY(promoter_id)
                    REFERENCES promoters(id)
                    ON DELETE SET NULL,

                FOREIGN KEY(student_id)
                    REFERENCES students(id)
                    ON DELETE SET NULL
            )
        """)

        # ==================================================
        # WITHDRAWALS
        # ==================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                promoter_id INTEGER NOT NULL,

                amount REAL NOT NULL,

                bank_name TEXT NOT NULL,

                bank_code TEXT NOT NULL,

                account_name TEXT NOT NULL,

                account_number TEXT NOT NULL,

                status TEXT NOT NULL DEFAULT 'pending',

                transfer_reference TEXT UNIQUE,

                transfer_id TEXT UNIQUE,

                transfer_status TEXT,

                transfer_message TEXT,

                created_at TEXT NOT NULL,

                FOREIGN KEY(promoter_id)
                    REFERENCES promoters(id)
                    ON DELETE CASCADE
            )
        """)

        # ==================================================
        # SAFE MIGRATIONS
        # ==================================================

        migrations = [

            (
                "promoters",
                "password_hash",
                "TEXT"
            ),

            (
                "promoters",
                "withdrawal_code_hash",
                "TEXT"
            ),

            (
                "withdrawals",
                "transfer_reference",
                "TEXT"
            ),

            (
                "withdrawals",
                "transfer_id",
                "TEXT"
            ),

            (
                "withdrawals",
                "transfer_status",
                "TEXT"
            ),

            (
                "withdrawals",
                "transfer_message",
                "TEXT"
            ),
        ]

        for table, column, column_type in migrations:

            columns = cursor.execute(
                f"PRAGMA table_info({table})"
            ).fetchall()

            existing = {
                row["name"]
                for row in columns
            }

            if column not in existing:

                cursor.execute(
                    f"""
                    ALTER TABLE {table}
                    ADD COLUMN {column} {column_type}
                    """
                )

        # ==================================================
        # INDEXES
        # ==================================================

        indexes = [

            """
            CREATE INDEX IF NOT EXISTS
            idx_students_telegram
            ON students(telegram_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_students_referral
            ON students(referral_code)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_promoters_referral
            ON promoters(referral_code)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_commissions_promoter
            ON commissions(promoter_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_commissions_tx_ref
            ON commissions(tx_ref)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_withdrawals_promoter
            ON withdrawals(promoter_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_withdrawals_status
            ON withdrawals(status)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_withdrawals_transfer_id
            ON withdrawals(transfer_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_withdrawals_transfer_reference
            ON withdrawals(transfer_reference)
            """,
        ]

        for statement in indexes:

            cursor.execute(statement)

        conn.commit()

        logger.info(
            "Database initialized successfully."
        )

    finally:

        conn.close()


# ==========================================================
# PROMOTER
# ==========================================================

def get_promoter_by_id(promoter_id):

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

    referral_code = str(
        referral_code
    ).strip()

    conn = get_connection()

    try:

        return conn.execute(
            """
            SELECT *
            FROM promoters
            WHERE referral_code = ?
              AND LOWER(status) = 'active'
            LIMIT 1
            """,
            (referral_code,)
        ).fetchone()

    finally:

        conn.close()


def get_all_promoters():

    conn = get_connection()

    try:

        return conn.execute(
            """
            SELECT *
            FROM promoters
            ORDER BY id DESC
            """
        ).fetchall()

    finally:

        conn.close()


# ==========================================================
# PROMOTER PASSWORD
# ==========================================================

def set_promoter_password(
    promoter_id,
    password
):

    if not password:

        raise ValueError(
            "Password is required."
        )

    password = str(password)

    if len(password) < 8:

        raise ValueError(
            "Password must contain at least 8 characters."
        )

    if len(password) > 200:

        raise ValueError(
            "Password is too long."
        )

    password_hash = generate_password_hash(
        password,
        method="scrypt"
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
                promoter_id,
            )
        )

        conn.commit()

        return cursor.rowcount == 1

    finally:

        conn.close()


def verify_promoter_password(
    promoter_id,
    password
):

    if not password:
        return False

    conn = get_connection()

    try:

        row = conn.execute(
            """
            SELECT password_hash

            FROM promoters

            WHERE id = ?

            LIMIT 1
            """,
            (promoter_id,)
        ).fetchone()

    finally:

        conn.close()

    if not row:
        return False

    password_hash = row["password_hash"]

    if not password_hash:
        return False

    try:

        return check_password_hash(
            password_hash,
            password
        )

    except Exception:

        logger.exception(
            "Password verification failed."
        )

        return False


# ==========================================================
# PROMOTER WITHDRAWAL CODE
# ==========================================================

def generate_withdrawal_code():

    """
    Generate secure human-readable code.

    Example:

        WD-7K4P-9X2M
    """

    alphabet = (
        "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    )

    part1 = "".join(
        secrets.choice(alphabet)
        for _ in range(4)
    )

    part2 = "".join(
        secrets.choice(alphabet)
        for _ in range(4)
    )

    return (
        f"WD-{part1}-{part2}"
    )


def set_promoter_withdrawal_code(
    promoter_id,
    withdrawal_code
):

    """
    Save withdrawal code as a secure hash.

    The plain code is NEVER stored.
    """

    if not withdrawal_code:

        raise ValueError(
            "Withdrawal code is required."
        )

    withdrawal_code = str(
        withdrawal_code
    ).strip().upper()

    if len(withdrawal_code) < 8:

        raise ValueError(
            "Invalid withdrawal code."
        )

    withdrawal_code_hash = (
        generate_password_hash(
            withdrawal_code,
            method="scrypt"
        )
    )

    conn = get_connection()

    try:

        cursor = conn.execute(
            """
            UPDATE promoters

            SET withdrawal_code_hash = ?

            WHERE id = ?
            """,
            (
                withdrawal_code_hash,
                promoter_id,
            )
        )

        conn.commit()

        return cursor.rowcount == 1

    finally:

        conn.close()


def verify_promoter_withdrawal_code(
    promoter_id,
    withdrawal_code
):

    """
    Verify promoter withdrawal code.
    """

    if not withdrawal_code:
        return False

    withdrawal_code = str(
        withdrawal_code
    ).strip().upper()

    conn = get_connection()

    try:

        row = conn.execute(
            """
            SELECT withdrawal_code_hash

            FROM promoters

            WHERE id = ?

            LIMIT 1
            """,
            (promoter_id,)
        ).fetchone()

    finally:

        conn.close()

    if not row:
        return False

    code_hash = row[
        "withdrawal_code_hash"
    ]

    if not code_hash:
        return False

    try:

        return check_password_hash(
            code_hash,
            withdrawal_code
        )

    except Exception:

        logger.exception(
            "Withdrawal code verification failed."
        )

        return False


def generate_and_set_withdrawal_code(
    promoter_id
):

    """
    Generate a new withdrawal code.

    The plain code is returned ONCE.

    Only the hash is stored in database.
    """

    conn = get_connection()

    try:

        for _ in range(20):

            withdrawal_code = (
                generate_withdrawal_code()
            )

            withdrawal_code_hash = (
                generate_password_hash(
                    withdrawal_code,
                    method="scrypt"
                )
            )

            cursor = conn.execute(
                """
                UPDATE promoters

                SET withdrawal_code_hash = ?

                WHERE id = ?
                """,
                (
                    withdrawal_code_hash,
                    promoter_id,
                )
            )

            if cursor.rowcount != 1:

                conn.rollback()

                raise ValueError(
                    "Promoter not found."
                )

            conn.commit()

            return withdrawal_code

        raise RuntimeError(
            "Could not generate withdrawal code."
        )

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ==========================================================
# ADD PROMOTER
# ==========================================================

def add_promoter(
    full_name,
    phone=None,
    email=None,
    referral_code=None,
    commission_rate=0,
    password=None,
):

    full_name = str(
        full_name or ""
    ).strip()

    if not full_name:

        raise ValueError(
            "Full name is required."
        )

    commission_rate = money(
        commission_rate
    )

    if (
        commission_rate < 0
        or commission_rate > 100
    ):

        raise ValueError(
            "Commission rate must be between 0 and 100."
        )

    # ------------------------------------------------------
    # PASSWORD
    # ------------------------------------------------------

    if password:

        password = str(password)

        if len(password) < 8:

            raise ValueError(
                "Password must contain at least 8 characters."
            )

        if len(password) > 200:

            raise ValueError(
                "Password is too long."
            )

        password_hash = (
            generate_password_hash(
                password,
                method="scrypt"
            )
        )

    else:

        password_hash = None

    # ------------------------------------------------------
    # WITHDRAWAL CODE
    # ------------------------------------------------------

    withdrawal_code = (
        generate_withdrawal_code()
    )

    withdrawal_code_hash = (
        generate_password_hash(
            withdrawal_code,
            method="scrypt"
        )
    )

    conn = get_connection()

    try:

        for _ in range(10):

            if referral_code:

                code = str(
                    referral_code
                ).strip()

            else:

                code = (
                    "ALHIKAM-"
                    + secrets.token_hex(5).upper()
                )

            try:

                cursor = conn.execute(
                    """
                    INSERT INTO promoters (
                        full_name,
                        phone,
                        email,
                        referral_code,
                        password_hash,
                        withdrawal_code_hash,
                        commission_rate,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        full_name,
                        phone,
                        email,
                        code,
                        password_hash,
                        withdrawal_code_hash,
                        float(commission_rate),
                        utc_now(),
                    )
                )

                conn.commit()

                return {
                    "id": cursor.lastrowid,
                    "withdrawal_code": withdrawal_code,
                    "referral_code": code,
                }

            except sqlite3.IntegrityError:

                if referral_code:

                    raise ValueError(
                        "Referral code already exists."
                    )

        raise RuntimeError(
            "Could not generate unique referral code."
        )

    finally:

        conn.close()


# ==========================================================
# PAYMENT
# ==========================================================

def save_payment(data):

    if not isinstance(data, dict):

        raise ValueError(
            "Payment data must be a dictionary."
        )

    tx_ref = str(
        data.get("tx_ref") or ""
    ).strip()

    if not tx_ref:

        raise ValueError(
            "Transaction reference is required."
        )

    amount = money(
        data.get("amount", 0)
    )

    if amount < 0:

        raise ValueError(
            "Payment amount cannot be negative."
        )

    transaction_id = data.get(
        "transaction_id"
    )

    payment_plan = (
        data.get("payment_plan")
        or data.get("plan_name")
        or ""
    )

    status = str(
        data.get("status")
        or "pending"
    ).strip().lower()

    referral_code = data.get(
        "referral_code"
    )

    promoter_id = data.get(
        "promoter_id"
    )

    commission = money(
        data.get("commission", 0)
    )

    telegram_username = data.get(
        "telegram_username"
    )

    telegram_id = data.get(
        "telegram_id"
    )

    conn = get_connection()

    try:

        conn.execute(
            "BEGIN IMMEDIATE"
        )

        existing = conn.execute(
            """
            SELECT id

            FROM payments

            WHERE tx_ref = ?

            LIMIT 1
            """,
            (tx_ref,)
        ).fetchone()

        if existing:

            conn.execute(
                """
                UPDATE payments

                SET
                    transaction_id =
                        COALESCE(
                            ?,
                            transaction_id
                        ),

                    payment_plan =
                        CASE
                            WHEN ? != ''
                            THEN ?
                            ELSE payment_plan
                        END,

                    amount = ?,

                    status = ?,

                    referral_code =
                        COALESCE(
                            ?,
                            referral_code
                        ),

                    promoter_id =
                        COALESCE(
                            ?,
                            promoter_id
                        ),

                    commission = ?,

                    telegram_username =
                        COALESCE(
                            ?,
                            telegram_username
                        ),

                    telegram_id =
                        COALESCE(
                            ?,
                            telegram_id
                        )

                WHERE tx_ref = ?
                """,
                (
                    transaction_id,

                    payment_plan,
                    payment_plan,

                    float(amount),

                    status,

                    referral_code,
                    promoter_id,

                    float(commission),

                    telegram_username,
                    telegram_id,

                    tx_ref,
                )
            )

            conn.commit()

            return existing["id"]

        cursor = conn.execute(
            """
            INSERT INTO payments (
                tx_ref,
                transaction_id,
                payment_plan,
                amount,
                status,
                referral_code,
                promoter_id,
                commission,
                telegram_username,
                telegram_id,
                registration_completed,
                created_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?
            )
            """,
            (
                tx_ref,
                transaction_id,
                payment_plan,
                float(amount),
                status,
                referral_code,
                promoter_id,
                float(commission),
                telegram_username,
                telegram_id,
                utc_now(),
            )
        )

        conn.commit()

        return cursor.lastrowid

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


def get_payment_by_tx_ref(tx_ref):

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
            (str(tx_ref).strip(),)
        ).fetchone()

    finally:

        conn.close()


def update_payment_status(
    tx_ref,
    status,
    transaction_id=None,
):

    if not tx_ref:

        raise ValueError(
            "Transaction reference is required."
        )

    status = str(
        status or ""
    ).strip().lower()

    if not status:

        raise ValueError(
            "Payment status is required."
        )

    conn = get_connection()

    try:

        cursor = conn.execute(
            """
            UPDATE payments

            SET
                status = ?,

                transaction_id =
                    COALESCE(
                        ?,
                        transaction_id
                    )

            WHERE tx_ref = ?
            """,
            (
                status,
                transaction_id,
                str(tx_ref).strip(),
            )
        )

        conn.commit()

        return cursor.rowcount > 0

    finally:

        conn.close()


# ==========================================================
# PAYMENT REGISTRATION
# ==========================================================

def mark_payment_registration_completed(
    tx_ref
):

    if not tx_ref:

        raise ValueError(
            "Transaction reference is required."
        )

    conn = get_connection()

    try:

        cursor = conn.execute(
            """
            UPDATE payments

            SET registration_completed = 1

            WHERE tx_ref = ?
            """,
            (str(tx_ref).strip(),)
        )

        conn.commit()

        return cursor.rowcount > 0

    finally:

        conn.close()


def payment_registration_completed(
    tx_ref
):

    if not tx_ref:
        return False

    conn = get_connection()

    try:

        row = conn.execute(
            """
            SELECT registration_completed

            FROM payments

            WHERE tx_ref = ?

            LIMIT 1
            """,
            (str(tx_ref).strip(),)
        ).fetchone()

        if not row:
            return False

        return bool(
            row["registration_completed"]
        )

    finally:

        conn.close()


# ==========================================================
# STUDENTS
# ==========================================================

def add_student(data):

    if not isinstance(data, dict):

        raise ValueError(
            "Student data must be a dictionary."
        )

    tx_ref = data.get("tx_ref")

    if tx_ref:

        tx_ref = str(
            tx_ref
        ).strip()

    full_name = str(
        data.get("full_name") or ""
    ).strip()

    phone = data.get("phone")

    email = data.get("email")

    telegram_username = data.get(
        "telegram_username"
    )

    telegram_id = data.get(
        "telegram_id"
    )

    payment_plan = (
        data.get("payment_plan")
        or data.get("plan_name")
        or ""
    )

    amount_paid = money(
        data.get(
            "amount_paid",
            data.get("amount", 0)
        )
    )

    payment_status = str(
        data.get("payment_status")
        or data.get("status")
        or "successful"
    ).strip().lower()

    payment_token = data.get(
        "payment_token"
    )

    referral_code = data.get(
        "referral_code"
    )

    promoter_id = data.get(
        "promoter_id"
    )

    conn = get_connection()

    try:

        conn.execute(
            "BEGIN IMMEDIATE"
        )

        if tx_ref:

            existing = conn.execute(
                """
                SELECT *

                FROM students

                WHERE tx_ref = ?

                LIMIT 1
                """,
                (tx_ref,)
            ).fetchone()

            if existing:

                conn.commit()

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
                payment_plan,
                amount_paid,
                payment_status,
                registration_completed,
                referral_code,
                promoter_id,
                created_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?
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
                payment_plan,
                float(amount_paid),
                payment_status,
                referral_code,
                promoter_id,
                utc_now(),
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


def get_student_by_tx_ref(tx_ref):

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
            (str(tx_ref).strip(),)
        ).fetchone()

    finally:

        conn.close()


# ==========================================================
# GET STUDENT BY TELEGRAM ID
# ==========================================================

def get_student_by_telegram_id(
    telegram_id
):

    """
    Find a registered student using Telegram user ID.

    Used by bot.py when a student sends /start
    without a TX_REF.
    """

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


def create_or_get_student(data):

    if not isinstance(data, dict):

        raise ValueError(
            "Student data must be a dictionary."
        )

    tx_ref = data.get("tx_ref")

    if tx_ref:

        tx_ref = str(
            tx_ref
        ).strip()

    conn = get_connection()

    try:

        conn.execute(
            "BEGIN IMMEDIATE"
        )

        if tx_ref:

            existing = conn.execute(
                """
                SELECT *

                FROM students

                WHERE tx_ref = ?

                LIMIT 1
                """,
                (tx_ref,)
            ).fetchone()

            if existing:

                conn.commit()

                return existing, False

        payment_token = data.get(
            "payment_token"
        )

        full_name = str(
            data.get("full_name") or ""
        ).strip()

        phone = data.get("phone")

        email = data.get("email")

        telegram_username = data.get(
            "telegram_username"
        )

        telegram_id = data.get(
            "telegram_id"
        )

        payment_plan = (
            data.get("payment_plan")
            or data.get("plan_name")
            or ""
        )

        amount_paid = money(
            data.get(
                "amount_paid",
                data.get("amount", 0)
            )
        )

        payment_status = str(
            data.get("payment_status")
            or data.get("status")
            or "successful"
        ).strip().lower()

        referral_code = data.get(
            "referral_code"
        )

        promoter_id = data.get(
            "promoter_id"
        )

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
                payment_plan,
                amount_paid,
                payment_status,
                registration_completed,
                referral_code,
                promoter_id,
                created_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?
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
                payment_plan,
                float(amount_paid),
                payment_status,
                referral_code,
                promoter_id,
                utc_now(),
            )
        )

        student_id = cursor.lastrowid

        student = conn.execute(
            """
            SELECT *

            FROM students

            WHERE id = ?

            LIMIT 1
            """,
            (student_id,)
        ).fetchone()

        conn.commit()

        return student, True

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ==========================================================
# COMMISSION CHECK
# ==========================================================

def commission_exists(tx_ref):

    if not tx_ref:
        return False

    conn = get_connection()

    try:

        row = conn.execute(
            """
            SELECT id

            FROM commissions

            WHERE tx_ref = ?

            LIMIT 1
            """,
            (str(tx_ref).strip(),)
        ).fetchone()

        return row is not None

    finally:

        conn.close()


# ==========================================================
# COMMISSION
# ==========================================================

def create_commission(
    tx_ref,
    promoter_id,
    student_id,
    payment_amount,
    commission_rate,
    commission_amount,
):

    if not tx_ref:

        raise ValueError(
            "Transaction reference required."
        )

    payment_amount = money(
        payment_amount
    )

    commission_rate = money(
        commission_rate
    )

    commission_amount = money(
        commission_amount
    )

    if payment_amount <= 0:

        raise ValueError(
            "Invalid payment amount."
        )

    if commission_amount < 0:

        raise ValueError(
            "Invalid commission amount."
        )

    conn = get_connection()

    try:

        conn.execute(
            "BEGIN IMMEDIATE"
        )

        existing = conn.execute(
            """
            SELECT id

            FROM commissions

            WHERE tx_ref = ?

            LIMIT 1
            """,
            (tx_ref,)
        ).fetchone()

        if existing:

            conn.commit()

            return existing["id"]

        promoter = conn.execute(
            """
            SELECT *

            FROM promoters

            WHERE id = ?

              AND LOWER(status) = 'active'

            LIMIT 1
            """,
            (promoter_id,)
        ).fetchone()

        if not promoter:

            conn.rollback()

            raise ValueError(
                "Promoter is not active."
            )

        cursor = conn.execute(
            """
            INSERT INTO commissions (
                tx_ref,
                promoter_id,
                student_id,
                payment_amount,
                commission_rate,
                commission_amount,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 'successful', ?)
            """,
            (
                tx_ref,
                promoter_id,
                student_id,
                float(payment_amount),
                float(commission_rate),
                float(commission_amount),
                utc_now(),
            )
        )

        conn.execute(
            """
            UPDATE promoters

            SET
                total_sales =
                    total_sales + ?,

                total_earned =
                    total_earned + ?,

                available_balance =
                    available_balance + ?

            WHERE id = ?
            """,
            (
                float(payment_amount),
                float(commission_amount),
                float(commission_amount),
                promoter_id,
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
# WITHDRAWAL
# ==========================================================

def create_withdrawal(
    promoter_id,
    amount,
    bank_name,
    bank_code,
    account_name,
    account_number,
):

    amount = money(amount)

    if amount < MINIMUM_WITHDRAWAL:

        raise ValueError(
            f"Minimum withdrawal is "
            f"₦{MINIMUM_WITHDRAWAL:,.2f}"
        )

    bank_name = str(
        bank_name or ""
    ).strip()

    bank_code = str(
        bank_code or ""
    ).strip()

    account_name = str(
        account_name or ""
    ).strip()

    account_number = str(
        account_number or ""
    ).strip()

    if not bank_name:

        raise ValueError(
            "Bank name is required."
        )

    if not bank_code:

        raise ValueError(
            "Bank code is required."
        )

    if not account_name:

        raise ValueError(
            "Account name is required."
        )

    if not account_number.isdigit():

        raise ValueError(
            "Account number must contain digits only."
        )

    if len(account_number) != 10:

        raise ValueError(
            "Account number must contain 10 digits."
        )

    conn = get_connection()

    try:

        conn.execute(
            "BEGIN IMMEDIATE"
        )

        promoter = conn.execute(
            """
            SELECT *

            FROM promoters

            WHERE id = ?

              AND LOWER(status) = 'active'

            LIMIT 1
            """,
            (promoter_id,)
        ).fetchone()

        if not promoter:

            conn.rollback()

            raise ValueError(
                "Promoter account is not active."
            )

        available = money(
            promoter["available_balance"]
        )

        if amount > available:

            conn.rollback()

            raise ValueError(
                "Insufficient available balance."
            )

        # --------------------------------------------------
        # RESERVE BALANCE
        # --------------------------------------------------

        cursor = conn.execute(
            """
            UPDATE promoters

            SET available_balance =
                available_balance - ?

            WHERE id = ?

              AND available_balance >= ?
            """,
            (
                float(amount),
                promoter_id,
                float(amount),
            )
        )

        if cursor.rowcount != 1:

            conn.rollback()

            raise ValueError(
                "Withdrawal balance could not be reserved."
            )

        # --------------------------------------------------
        # CREATE WITHDRAWAL
        # --------------------------------------------------

        cursor = conn.execute(
            """
            INSERT INTO withdrawals (
                promoter_id,
                amount,
                bank_name,
                bank_code,
                account_name,
                account_number,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                promoter_id,
                float(amount),
                bank_name,
                bank_code,
                account_name,
                account_number,
                utc_now(),
            )
        )

        withdrawal_id = cursor.lastrowid

        conn.commit()

        return withdrawal_id

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ==========================================================
# WITHDRAWAL LOOKUPS
# ==========================================================

def get_all_withdrawals():

    conn = get_connection()

    try:

        return conn.execute(
            """
            SELECT
                w.*,

                p.full_name AS promoter_name,

                p.referral_code

            FROM withdrawals w

            JOIN promoters p
              ON p.id = w.promoter_id

            ORDER BY w.id DESC
            """
        ).fetchall()

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


def get_withdrawal_by_transfer_id(
    transfer_id
):

    if not transfer_id:
        return None

    conn = get_connection()

    try:

        return conn.execute(
            """
            SELECT *

            FROM withdrawals

            WHERE transfer_id = ?

            LIMIT 1
            """,
            (str(transfer_id),)
        ).fetchone()

    finally:

        conn.close()


def get_withdrawal_by_transfer_reference(
    transfer_reference
):

    if not transfer_reference:
        return None

    conn = get_connection()

    try:

        return conn.execute(
            """
            SELECT *

            FROM withdrawals

            WHERE transfer_reference = ?

            LIMIT 1
            """,
            (str(transfer_reference),)
        ).fetchone()

    finally:

        conn.close()


def get_promoter_withdrawals(
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
# TRANSFER UPDATE
# ==========================================================

def update_withdrawal_transfer(
    withdrawal_id,
    transfer_id=None,
    transfer_reference=None,
    transfer_status=None,
    transfer_message=None,
):

    conn = get_connection()

    try:

        conn.execute(
            "BEGIN IMMEDIATE"
        )

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

            conn.rollback()

            raise ValueError(
                "Withdrawal not found."
            )

        if withdrawal["status"] in {
            "successful",
            "failed",
            "cancelled",
        }:

            conn.commit()

            return False

        # --------------------------------------------------
        # TRANSFER ID COLLISION
        # --------------------------------------------------

        if transfer_id:

            existing = conn.execute(
                """
                SELECT id

                FROM withdrawals

                WHERE transfer_id = ?

                  AND id != ?

                LIMIT 1
                """,
                (
                    str(transfer_id),
                    withdrawal_id,
                )
            ).fetchone()

            if existing:

                conn.rollback()

                raise ValueError(
                    "Transfer ID already belongs "
                    "to another withdrawal."
                )

        # --------------------------------------------------
        # REFERENCE COLLISION
        # --------------------------------------------------

        if transfer_reference:

            existing = conn.execute(
                """
                SELECT id

                FROM withdrawals

                WHERE transfer_reference = ?

                  AND id != ?

                LIMIT 1
                """,
                (
                    str(transfer_reference),
                    withdrawal_id,
                )
            ).fetchone()

            if existing:

                conn.rollback()

                raise ValueError(
                    "Transfer reference already "
                    "belongs to another withdrawal."
                )

        new_status = withdrawal["status"]

        if new_status == "pending":

            new_status = "processing"

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

                transfer_status =
                    COALESCE(
                        ?,
                        transfer_status
                    ),

                transfer_message =
                    COALESCE(
                        ?,
                        transfer_message
                    ),

                status = ?

            WHERE id = ?
            """,
            (
                str(transfer_id)
                if transfer_id is not None
                else None,

                str(transfer_reference)
                if transfer_reference is not None
                else None,

                str(transfer_status)
                if transfer_status is not None
                else None,

                str(transfer_message)
                if transfer_message is not None
                else None,

                new_status,

                withdrawal_id,
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
# MARK SUCCESSFUL
# ==========================================================

def mark_withdrawal_successful(
    withdrawal_id,
    transfer_id=None,
    transfer_reference=None,
    transfer_message=None,
):

    conn = get_connection()

    try:

        conn.execute(
            "BEGIN IMMEDIATE"
        )

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

            conn.rollback()

            raise ValueError(
                "Withdrawal not found."
            )

        # --------------------------------------------------
        # IDEMPOTENT SUCCESS
        # --------------------------------------------------

        if withdrawal["status"] == "successful":

            conn.commit()

            return True

        # --------------------------------------------------
        # NEVER RESURRECT FAILED/CANCELLED
        # --------------------------------------------------

        if withdrawal["status"] in {
            "failed",
            "cancelled",
        }:

            conn.rollback()

            raise ValueError(
                "A failed or cancelled withdrawal "
                "cannot become successful."
            )

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

                transfer_status = 'SUCCESSFUL',

                transfer_message =
                    COALESCE(
                        ?,
                        transfer_message
                    )

            WHERE id = ?
            """,
            (
                str(transfer_id)
                if transfer_id is not None
                else None,

                str(transfer_reference)
                if transfer_reference is not None
                else None,

                str(transfer_message)
                if transfer_message is not None
                else None,

                withdrawal_id,
            )
        )

        # --------------------------------------------------
        # MONEY WAS ALREADY RESERVED.
        # ONLY INCREMENT WITHDRAWN AMOUNT.
        # --------------------------------------------------

        conn.execute(
            """
            UPDATE promoters

            SET withdrawn_amount =
                withdrawn_amount + ?

            WHERE id = ?
            """,
            (
                float(
                    money(
                        withdrawal["amount"]
                    )
                ),

                withdrawal["promoter_id"],
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
# REFUND FAILED/CANCELLED WITHDRAWAL
# ==========================================================

def refund_withdrawal(
    withdrawal_id,
    final_status="failed",
    transfer_id=None,
    transfer_reference=None,
    transfer_message=None,
):

    if final_status not in {
        "failed",
        "cancelled",
    }:

        raise ValueError(
            "Invalid refund status."
        )

    conn = get_connection()

    try:

        conn.execute(
            "BEGIN IMMEDIATE"
        )

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

            conn.rollback()

            raise ValueError(
                "Withdrawal not found."
            )

        # --------------------------------------------------
        # ALREADY FINAL
        # --------------------------------------------------

        if withdrawal["status"] in {
            "failed",
            "cancelled",
        }:

            conn.commit()

            return True

        if withdrawal["status"] == "successful":

            conn.rollback()

            raise ValueError(
                "Successful withdrawal cannot be refunded."
            )

        amount = money(
            withdrawal["amount"]
        )

        # --------------------------------------------------
        # RETURN RESERVED MONEY
        # --------------------------------------------------

        conn.execute(
            """
            UPDATE promoters

            SET available_balance =
                available_balance + ?

            WHERE id = ?
            """,
            (
                float(amount),
                withdrawal["promoter_id"],
            )
        )

        # --------------------------------------------------
        # FINAL STATUS
        # --------------------------------------------------

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

                transfer_status = ?,

                transfer_message =
                    COALESCE(
                        ?,
                        transfer_message
                    )

            WHERE id = ?
            """,
            (
                final_status,

                str(transfer_id)
                if transfer_id is not None
                else None,

                str(transfer_reference)
                if transfer_reference is not None
                else None,

                final_status.upper(),

                str(transfer_message)
                if transfer_message is not None
                else None,

                withdrawal_id,
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
# UPDATE WITHDRAWAL STATUS
# ==========================================================

def update_withdrawal_status(
    withdrawal_id,
    status,
    transfer_id=None,
    transfer_reference=None,
    message=None,
):

    status = str(
        status or ""
    ).upper()

    if status in {
        "SUCCESS",
        "SUCCESSFUL",
        "COMPLETED",
    }:

        return mark_withdrawal_successful(
            withdrawal_id=withdrawal_id,
            transfer_id=transfer_id,
            transfer_reference=transfer_reference,
            transfer_message=message,
        )

    if status in {
        "FAILED",
        "CANCELLED",
        "CANCELED",
        "REJECTED",
    }:

        final_status = (
            "cancelled"
            if status in {
                "CANCELLED",
                "CANCELED",
            }
            else "failed"
        )

        return refund_withdrawal(
            withdrawal_id=withdrawal_id,
            final_status=final_status,
            transfer_id=transfer_id,
            transfer_reference=transfer_reference,
            transfer_message=message,
        )

    return update_withdrawal_transfer(
        withdrawal_id=withdrawal_id,
        transfer_id=transfer_id,
        transfer_reference=transfer_reference,
        transfer_status=status,
        transfer_message=message,
    )


# ==========================================================
# TRUSTED FLUTTERWAVE RESULT
# ==========================================================

def process_transfer_result(
    withdrawal_id,
    flutterwave_status,
    transfer_id=None,
    transfer_reference=None,
    message=None,
):

    """
    IMPORTANT:

    flutterwave_status MUST come from a trusted
    server-side Flutterwave API verification.

    Never trust status supplied directly by browser.
    """

    status = str(
        flutterwave_status or ""
    ).strip().upper()

    if not status:

        raise ValueError(
            "Flutterwave transfer status is required."
        )

    # --------------------------------------------------
    # SUCCESS
    # --------------------------------------------------

    if status in {
        "SUCCESS",
        "SUCCESSFUL",
        "COMPLETED",
    }:

        return mark_withdrawal_successful(
            withdrawal_id=withdrawal_id,
            transfer_id=transfer_id,
            transfer_reference=transfer_reference,
            transfer_message=message,
        )

    # --------------------------------------------------
    # FAILED
    # --------------------------------------------------

    if status in {
        "FAILED",
        "CANCELLED",
        "CANCELED",
        "REJECTED",
    }:

        final_status = (
            "cancelled"
            if status in {
                "CANCELLED",
                "CANCELED",
            }
            else "failed"
        )

        return refund_withdrawal(
            withdrawal_id=withdrawal_id,
            final_status=final_status,
            transfer_id=transfer_id,
            transfer_reference=transfer_reference,
            transfer_message=message,
        )

    # --------------------------------------------------
    # UNKNOWN / PROCESSING
    # --------------------------------------------------

    return update_withdrawal_transfer(
        withdrawal_id=withdrawal_id,
        transfer_id=transfer_id,
        transfer_reference=transfer_reference,
        transfer_status=status,
        transfer_message=message,
    )


# ==========================================================
# INITIALIZE
# ==========================================================

initialize_database()