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
# ==========================================================

import sqlite3

from config import DATABASE_NAME


# ==========================================================
# CONNECTION
# ==========================================================

def get_connection():

    conn = sqlite3.connect(
        DATABASE_NAME,
        check_same_thread=False,
        timeout=30
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
# DATABASE MIGRATION HELPERS
# ==========================================================

def _column_exists(
    cursor,
    table_name,
    column_name
):

    cursor.execute(
        f"PRAGMA table_info({table_name})"
    )

    columns = cursor.fetchall()

    return any(
        column["name"] == column_name
        for column in columns
    )


def _add_column_if_missing(
    cursor,
    table_name,
    column_name,
    column_definition
):

    if not _column_exists(
        cursor,
        table_name,
        column_name
    ):

        cursor.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name}
            {column_definition}
            """
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

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS promoters (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            full_name TEXT NOT NULL,

            phone TEXT,

            email TEXT,

            referral_code TEXT UNIQUE NOT NULL,

            commission_rate REAL DEFAULT 20,

            total_sales INTEGER DEFAULT 0,

            total_earned REAL DEFAULT 0,

            available_balance REAL DEFAULT 0,

            withdrawn_amount REAL DEFAULT 0,

            status TEXT DEFAULT 'active',

            created_at
                TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

            full_name TEXT NOT NULL,

            phone TEXT,

            email TEXT,

            course TEXT,

            telegram_id TEXT,

            telegram_username TEXT,

            telegram_name TEXT,

            payment_plan TEXT,

            amount_paid REAL DEFAULT 0,

            payment_status TEXT DEFAULT 'Pending',

            registration_completed INTEGER DEFAULT 0,

            referral_code TEXT,

            promoter_id INTEGER,

            created_at
                TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (promoter_id)
                REFERENCES promoters(id)
        )
        """)

        # ==================================================
        # PAYMENTS
        # ==================================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            tx_ref TEXT UNIQUE NOT NULL,

            transaction_id TEXT,

            payment_plan TEXT,

            amount REAL DEFAULT 0,

            payment_status TEXT DEFAULT 'Pending',

            referral_code TEXT,

            promoter_id INTEGER,

            promoter_name TEXT,

            commission REAL DEFAULT 0,

            telegram_id TEXT,

            telegram_username TEXT,

            telegram_name TEXT,

            registration_completed INTEGER DEFAULT 0,

            created_at
                TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (promoter_id)
                REFERENCES promoters(id)
        )
        """)

        # ==================================================
        # COMMISSIONS
        # ==================================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS commissions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            promoter_id INTEGER NOT NULL,

            student_id INTEGER,

            tx_ref TEXT UNIQUE NOT NULL,

            payment_amount REAL DEFAULT 0,

            commission_rate REAL DEFAULT 0,

            commission_amount REAL DEFAULT 0,

            status TEXT DEFAULT 'available',

            created_at
                TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (promoter_id)
                REFERENCES promoters(id),

            FOREIGN KEY (student_id)
                REFERENCES students(id)
        )
        """)

        # ==================================================
        # WITHDRAWALS
        # ==================================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            promoter_id INTEGER NOT NULL,

            amount REAL DEFAULT 0,

            bank_name TEXT NOT NULL,

            bank_code TEXT,

            account_name TEXT NOT NULL,

            account_number TEXT NOT NULL,

            status TEXT DEFAULT 'pending',

            transfer_reference TEXT,

            transfer_id TEXT,

            transfer_status TEXT,

            transfer_message TEXT,

            created_at
                TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (promoter_id)
                REFERENCES promoters(id)
        )
        """)

        # ==================================================
        # MIGRATE OLD DATABASE
        # ==================================================

        _add_column_if_missing(
            cursor,
            "withdrawals",
            "bank_code",
            "TEXT"
        )

        _add_column_if_missing(
            cursor,
            "withdrawals",
            "transfer_reference",
            "TEXT"
        )

        _add_column_if_missing(
            cursor,
            "withdrawals",
            "transfer_id",
            "TEXT"
        )

        _add_column_if_missing(
            cursor,
            "withdrawals",
            "transfer_status",
            "TEXT"
        )

        _add_column_if_missing(
            cursor,
            "withdrawals",
            "transfer_message",
            "TEXT"
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
            idx_students_promoter
            ON students(promoter_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_payments_status
            ON payments(payment_status)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_payments_promoter
            ON payments(promoter_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_promoters_referral
            ON promoters(referral_code)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_promoters_status
            ON promoters(status)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_commissions_promoter
            ON commissions(promoter_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_commissions_student
            ON commissions(student_id)
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
            idx_withdrawals_transfer_reference
            ON withdrawals(transfer_reference)
            """
        ]

        for sql in indexes:

            cursor.execute(sql)

        conn.commit()

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ==========================================================
# STUDENT
# ==========================================================

def add_student(data):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO students (

            payment_token,
            tx_ref,
            full_name,
            phone,
            email,
            course,
            telegram_id,
            telegram_username,
            telegram_name,
            payment_plan,
            amount_paid,
            payment_status,
            registration_completed,
            referral_code,
            promoter_id

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            data.get("payment_token", ""),

            data.get("tx_ref", ""),

            data.get("full_name", ""),

            data.get("phone", ""),

            data.get("email", ""),

            data.get("course", ""),

            str(
                data.get("telegram_id", "")
                or ""
            ),

            data.get(
                "telegram_username",
                ""
            ),

            data.get(
                "telegram_name",
                ""
            ),

            data.get(
                "payment_plan",
                ""
            ),

            float(
                data.get(
                    "amount_paid",
                    0
                )
                or 0
            ),

            data.get(
                "payment_status",
                "Pending"
            ),

            int(
                data.get(
                    "registration_completed",
                    0
                )
                or 0
            ),

            data.get(
                "referral_code",
                ""
            ),

            data.get("promoter_id")

        ))

        student_id = cursor.lastrowid

        conn.commit()

        return student_id

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ==========================================================
# GET STUDENT BY ID
# ==========================================================

def get_student_by_id(student_id):

    if not student_id:
        return None

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM students
        WHERE id=?
        LIMIT 1
        """, (student_id,))

        return cursor.fetchone()

    finally:

        conn.close()


# ==========================================================
# GET STUDENT BY TELEGRAM ID
# ==========================================================

def get_student_by_telegram_id(telegram_id):

    if not telegram_id:
        return None

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM students
        WHERE telegram_id=?
        ORDER BY id DESC
        LIMIT 1
        """, (
            str(telegram_id),
        ))

        return cursor.fetchone()

    finally:

        conn.close()


# ==========================================================
# GET STUDENT BY TX REF
# ==========================================================

def get_student_by_tx_ref(tx_ref):

    if not tx_ref:
        return None

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM students
        WHERE tx_ref=?
        LIMIT 1
        """, (tx_ref,))

        return cursor.fetchone()

    finally:

        conn.close()


# ==========================================================
# PROMOTER
# ==========================================================

def get_promoter_by_referral_code(
    referral_code
):

    if not referral_code:
        return None

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM promoters
        WHERE referral_code=?
        AND LOWER(status)='active'
        LIMIT 1
        """, (
            referral_code.strip(),
        ))

        return cursor.fetchone()

    finally:

        conn.close()


# ==========================================================
# GET PROMOTER BY ID
# ==========================================================

def get_promoter_by_id(promoter_id):

    if not promoter_id:
        return None

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM promoters
        WHERE id=?
        LIMIT 1
        """, (promoter_id,))

        return cursor.fetchone()

    finally:

        conn.close()


# ==========================================================
# ADD PROMOTER
# ==========================================================

def add_promoter(
    full_name,
    phone,
    email,
    referral_code,
    commission_rate=20
):

    full_name = (
        full_name or ""
    ).strip()

    referral_code = (
        referral_code or ""
    ).strip()

    if not full_name:

        raise ValueError(
            "Promoter full name is required."
        )

    if not referral_code:

        raise ValueError(
            "Referral code is required."
        )

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO promoters (

            full_name,
            phone,
            email,
            referral_code,
            commission_rate

        )

        VALUES (?, ?, ?, ?, ?)
        """, (

            full_name,
            phone,
            email,
            referral_code,

            float(
                commission_rate or 20
            )

        ))

        promoter_id = cursor.lastrowid

        conn.commit()

        return promoter_id

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ==========================================================
# PAYMENT
# ==========================================================

def save_payment(data):

    tx_ref = (
        data.get("tx_ref", "")
        or ""
    ).strip()

    if not tx_ref:

        raise ValueError(
            "tx_ref is required."
        )

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
        SELECT registration_completed
        FROM payments
        WHERE tx_ref=?
        LIMIT 1
        """, (tx_ref,))

        existing = cursor.fetchone()

        if existing:

            registration_completed = int(
                existing["registration_completed"]
                or 0
            )

        else:

            registration_completed = int(
                data.get(
                    "registration_completed",
                    0
                )
                or 0
            )

        cursor.execute("""
        INSERT INTO payments (

            tx_ref,
            transaction_id,
            payment_plan,
            amount,
            payment_status,
            referral_code,
            promoter_id,
            promoter_name,
            commission,
            telegram_id,
            telegram_username,
            telegram_name,
            registration_completed

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(tx_ref)

        DO UPDATE SET

            transaction_id =
                excluded.transaction_id,

            payment_plan =
                excluded.payment_plan,

            amount =
                excluded.amount,

            payment_status =
                excluded.payment_status,

            referral_code =
                excluded.referral_code,

            promoter_id =
                excluded.promoter_id,

            promoter_name =
                excluded.promoter_name,

            commission =
                excluded.commission,

            telegram_id =
                excluded.telegram_id,

            telegram_username =
                excluded.telegram_username,

            telegram_name =
                excluded.telegram_name,

            registration_completed =
                excluded.registration_completed

        """, (

            tx_ref,

            data.get(
                "transaction_id",
                ""
            ),

            data.get(
                "payment_plan",
                ""
            ),

            float(
                data.get(
                    "amount",
                    0
                )
                or 0
            ),

            data.get(
                "payment_status",
                "Pending"
            ),

            data.get(
                "referral_code",
                ""
            ),

            data.get(
                "promoter_id"
            ),

            data.get(
                "promoter_name",
                ""
            ),

            float(
                data.get(
                    "commission",
                    0
                )
                or 0
            ),

            str(
                data.get(
                    "telegram_id",
                    ""
                )
                or ""
            ),

            data.get(
                "telegram_username",
                ""
            ),

            data.get(
                "telegram_name",
                ""
            ),

            registration_completed

        ))

        conn.commit()

        return True

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ==========================================================
# GET PAYMENT
# ==========================================================

def get_payment_by_tx_ref(tx_ref):

    if not tx_ref:
        return None

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM payments
        WHERE tx_ref=?
        LIMIT 1
        """, (tx_ref,))

        return cursor.fetchone()

    finally:

        conn.close()


# ==========================================================
# UPDATE PAYMENT STATUS
# ==========================================================

def update_payment_status(
    tx_ref,
    status,
    transaction_id=None
):

    if not tx_ref:
        return False

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
        UPDATE payments

        SET

            payment_status=?,

            transaction_id =
                COALESCE(
                    ?,
                    transaction_id
                )

        WHERE tx_ref=?
        """, (
            status,
            transaction_id,
            tx_ref
        ))

        changed = (
            cursor.rowcount > 0
        )

        conn.commit()

        return changed

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ==========================================================
# MARK REGISTRATION COMPLETED
# ==========================================================

def mark_payment_registration_completed(
    tx_ref
):

    if not tx_ref:
        return False

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
        UPDATE payments

        SET registration_completed=1

        WHERE tx_ref=?
        """, (tx_ref,))

        changed = (
            cursor.rowcount > 0
        )

        conn.commit()

        return changed

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ==========================================================
# COMMISSION EXISTS
# ==========================================================

def commission_exists(tx_ref):

    if not tx_ref:
        return False

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
        SELECT id
        FROM commissions
        WHERE tx_ref=?
        LIMIT 1
        """, (tx_ref,))

        return (
            cursor.fetchone()
            is not None
        )

    finally:

        conn.close()


# ==========================================================
# GET COMMISSION
# ==========================================================

def get_commission_by_tx_ref(tx_ref):

    if not tx_ref:
        return None

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM commissions
        WHERE tx_ref=?
        LIMIT 1
        """, (tx_ref,))

        return cursor.fetchone()

    finally:

        conn.close()


# ==========================================================
# CREATE COMMISSION
# ==========================================================

def create_commission(
    promoter_id,
    student_id,
    tx_ref,
    payment_amount,
    commission_amount
):

    if not promoter_id:

        raise ValueError(
            "Promoter ID is required."
        )

    if not tx_ref:

        raise ValueError(
            "Transaction reference is required."
        )

    payment_amount = float(
        payment_amount or 0
    )

    commission_amount = float(
        commission_amount or 0
    )

    if payment_amount <= 0:

        raise ValueError(
            "Payment amount must be greater than zero."
        )

    if commission_amount <= 0:

        raise ValueError(
            "Commission amount must be greater than zero."
        )

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            "BEGIN IMMEDIATE"
        )

        # --------------------------------------------------
        # DUPLICATE
        # --------------------------------------------------

        cursor.execute("""
        SELECT *
        FROM commissions
        WHERE tx_ref=?
        LIMIT 1
        """, (tx_ref,))

        existing = cursor.fetchone()

        if existing:

            conn.commit()

            return {
                "commission_id":
                    existing["id"],

                "commission_amount":
                    float(
                        existing[
                            "commission_amount"
                        ]
                        or 0
                    )
            }

        # --------------------------------------------------
        # PROMOTER
        # --------------------------------------------------

        cursor.execute("""
        SELECT
            id,
            commission_rate,
            status

        FROM promoters

        WHERE id=?
        LIMIT 1
        """, (promoter_id,))

        promoter = cursor.fetchone()

        if not promoter:

            raise ValueError(
                "Promoter not found."
            )

        if (
            str(
                promoter["status"]
            ).lower()
            != "active"
        ):

            raise ValueError(
                "Promoter account is not active."
            )

        # --------------------------------------------------
        # RATE
        # --------------------------------------------------

        commission_rate = (
            commission_amount /
            payment_amount
        ) * 100

        # --------------------------------------------------
        # CREATE COMMISSION
        # --------------------------------------------------

        cursor.execute("""
        INSERT INTO commissions (

            promoter_id,
            student_id,
            tx_ref,
            payment_amount,
            commission_rate,
            commission_amount,
            status

        )

        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (

            promoter_id,
            student_id,
            tx_ref,
            payment_amount,
            commission_rate,
            commission_amount,
            "available"

        ))

        commission_id = cursor.lastrowid

        # --------------------------------------------------
        # UPDATE PROMOTER
        # --------------------------------------------------

        cursor.execute("""
        UPDATE promoters

        SET

            total_sales =
                total_sales + 1,

            total_earned =
                total_earned + ?,

            available_balance =
                available_balance + ?

        WHERE id=?
        AND LOWER(status)='active'
        """, (

            commission_amount,
            commission_amount,
            promoter_id

        ))

        if cursor.rowcount != 1:

            raise ValueError(
                "Promoter balance could not be updated."
            )

        conn.commit()

        return {

            "commission_id":
                commission_id,

            "commission_amount":
                commission_amount

        }

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ==========================================================
# LINK COMMISSION TO STUDENT
# ==========================================================

def link_commission_to_student(
    tx_ref,
    student_id
):

    if not tx_ref or not student_id:
        return False

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
        UPDATE commissions

        SET student_id=?

        WHERE tx_ref=?

        AND (
            student_id IS NULL
            OR student_id=?
        )
        """, (
            student_id,
            tx_ref,
            student_id
        ))

        changed = (
            cursor.rowcount > 0
        )

        conn.commit()

        return changed

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ==========================================================
# CREATE WITHDRAWAL
# ==========================================================
#
# MINIMUM WITHDRAWAL = ₦200
#
# Balance is reserved immediately.
#
# SUCCESS:
#     reserved money becomes withdrawn.
#
# FAILED/CANCELLED:
#     reserved money returns to balance.
#
# ==========================================================

def create_withdrawal(
    promoter_id,
    amount,
    bank_name,
    account_name,
    account_number,
    bank_code=None
):

    if not promoter_id:

        raise ValueError(
            "Promoter ID is required."
        )

    try:

        amount = float(
            amount or 0
        )

    except Exception:

        raise ValueError(
            "Invalid withdrawal amount."
        )

    # ======================================================
    # MINIMUM WITHDRAWAL
    # ======================================================

    if amount < 200:

        raise ValueError(
            "Minimum withdrawal is ₦200."
        )

    # ======================================================
    # CLEAN INPUT
    # ======================================================

    bank_name = (
        bank_name or ""
    ).strip()

    bank_code = (
        bank_code or ""
    ).strip()

    account_name = (
        account_name or ""
    ).strip()

    account_number = (
        account_number or ""
    ).strip()

    # ======================================================
    # VALIDATION
    # ======================================================

    if not bank_name:

        raise ValueError(
            "Bank name is required."
        )

    if not account_name:

        raise ValueError(
            "Account name is required."
        )

    if (
        len(account_number) != 10
        or not account_number.isdigit()
    ):

        raise ValueError(
            "Account number must contain exactly 10 digits."
        )

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            "BEGIN IMMEDIATE"
        )

        # ==================================================
        # GET PROMOTER
        # ==================================================

        cursor.execute("""
        SELECT
            id,
            available_balance,
            status

        FROM promoters

        WHERE id=?
        LIMIT 1
        """, (promoter_id,))

        promoter = cursor.fetchone()

        if not promoter:

            raise ValueError(
                "Promoter not found."
            )

        if (
            str(
                promoter["status"]
            ).lower()
            != "active"
        ):

            raise ValueError(
                "Promoter account is not active."
            )

        balance = float(
            promoter["available_balance"]
            or 0
        )

        if amount > balance:

            raise ValueError(
                "Insufficient available balance."
            )

        # ==================================================
        # RESERVE BALANCE
        # ==================================================

        cursor.execute("""
        UPDATE promoters

        SET available_balance =
            available_balance - ?

        WHERE id=?

        AND LOWER(status)='active'

        AND available_balance >= ?
        """, (

            amount,
            promoter_id,
            amount

        ))

        if cursor.rowcount != 1:

            raise ValueError(
                "Unable to reserve withdrawal amount."
            )

        # ==================================================
        # CREATE WITHDRAWAL
        # ==================================================

        cursor.execute("""
        INSERT INTO withdrawals (

            promoter_id,
            amount,
            bank_name,
            bank_code,
            account_name,
            account_number,
            status,
            transfer_reference,
            transfer_id,
            transfer_status,
            transfer_message

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            promoter_id,
            amount,
            bank_name,
            bank_code,
            account_name,
            account_number,

            "pending",

            None,
            None,
            None,
            None

        ))

        withdrawal_id = (
            cursor.lastrowid
        )

        conn.commit()

        return withdrawal_id

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ==========================================================
# GET WITHDRAWAL
# ==========================================================

def get_withdrawal_by_id(
    withdrawal_id
):

    if not withdrawal_id:
        return None

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM withdrawals
        WHERE id=?
        LIMIT 1
        """, (withdrawal_id,))

        return cursor.fetchone()

    finally:

        conn.close()


# ==========================================================
# GET PROMOTER WITHDRAWALS
# ==========================================================

def get_promoter_withdrawals(
    promoter_id
):

    if not promoter_id:
        return []

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM withdrawals

        WHERE promoter_id=?

        ORDER BY id DESC
        """, (promoter_id,))

        return cursor.fetchall()

    finally:

        conn.close()


# ==========================================================
# UPDATE TRANSFER INFORMATION
# ==========================================================

def update_withdrawal_transfer(
    withdrawal_id,
    transfer_reference=None,
    transfer_id=None,
    transfer_status=None,
    transfer_message=None
):

    if not withdrawal_id:

        raise ValueError(
            "Withdrawal ID is required."
        )

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
        UPDATE withdrawals

        SET

            transfer_reference =
                COALESCE(
                    ?,
                    transfer_reference
                ),

            transfer_id =
                COALESCE(
                    ?,
                    transfer_id
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
                )

        WHERE id=?
        """, (

            transfer_reference,
            transfer_id,
            transfer_status,
            transfer_message,
            withdrawal_id

        ))

        changed = (
            cursor.rowcount > 0
        )

        conn.commit()

        return changed

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()

# ==========================================================
# MARK WITHDRAWAL SUCCESSFUL
# ==========================================================

def mark_withdrawal_successful(
    withdrawal_id,
    transfer_id=None,
    transfer_reference=None,
    transfer_message=None
):

    if not withdrawal_id:

        raise ValueError(
            "Withdrawal ID is required."
        )

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            "BEGIN IMMEDIATE"
        )


        # ==================================================
        # GET WITHDRAWAL
        # ==================================================

        cursor.execute("""
        SELECT *
        FROM withdrawals
        WHERE id=?
        LIMIT 1
        """, (
            withdrawal_id,
        ))

        withdrawal = cursor.fetchone()


        if not withdrawal:

            raise ValueError(
                "Withdrawal not found."
            )


        old_status = str(
            withdrawal["status"]
            or ""
        ).lower().strip()


        amount = float(
            withdrawal["amount"]
            or 0
        )


        promoter_id = (
            withdrawal["promoter_id"]
        )


        # ==================================================
        # ALREADY SUCCESSFUL
        # ==================================================

        if old_status == "successful":

            cursor.execute("""
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
                    'successful',

                transfer_message =
                    COALESCE(
                        ?,
                        transfer_message
                    )

            WHERE id=?
            """, (

                transfer_id,
                transfer_reference,
                transfer_message,
                withdrawal_id

            ))

            conn.commit()

            return True


        # ==================================================
        # ALREADY FAILED
        # ==================================================

        if old_status in {
            "failed",
            "cancelled"
        }:

            raise ValueError(
                "Withdrawal has already been finalized."
            )


        # ==================================================
        # UPDATE PROMOTER
        #
        # available_balance was already reduced
        # when withdrawal was created.
        #
        # Here we only add to withdrawn_amount.
        # ==================================================

        cursor.execute("""
        UPDATE promoters

        SET withdrawn_amount =
            withdrawn_amount + ?

        WHERE id=?
        """, (

            amount,
            promoter_id

        ))


        if cursor.rowcount != 1:

            raise ValueError(
                "Could not update withdrawn amount."
            )


        # ==================================================
        # FINALIZE WITHDRAWAL
        # ==================================================

        cursor.execute("""
        UPDATE withdrawals

        SET

            status='successful',

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

            transfer_status='successful',

            transfer_message =
                COALESCE(
                    ?,
                    transfer_message
                )

        WHERE id=?

        AND status IN (
            'pending',
            'processing'
        )
        """, (

            transfer_id,
            transfer_reference,
            transfer_message,
            withdrawal_id

        ))


        if cursor.rowcount != 1:

            raise ValueError(
                "Withdrawal could not be marked successful."
            )


        conn.commit()

        return True


    except Exception:

        conn.rollback()

        raise


    finally:

        conn.close()


# ==========================================================
# REFUND WITHDRAWAL
# ==========================================================

def refund_withdrawal(
    withdrawal_id,
    transfer_status="failed",
    transfer_message=None
):

    if not withdrawal_id:

        raise ValueError(
            "Withdrawal ID is required."
        )


    transfer_status = (
        transfer_status
        or "failed"
    ).strip().lower()


    if transfer_status not in {
        "failed",
        "cancelled"
    }:

        transfer_status = "failed"


    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            "BEGIN IMMEDIATE"
        )


        # ==================================================
        # GET WITHDRAWAL
        # ==================================================

        cursor.execute("""
        SELECT *
        FROM withdrawals
        WHERE id=?
        LIMIT 1
        """, (
            withdrawal_id,
        ))

        withdrawal = cursor.fetchone()


        if not withdrawal:

            raise ValueError(
                "Withdrawal not found."
            )


        old_status = str(
            withdrawal["status"]
            or ""
        ).lower().strip()


        amount = float(
            withdrawal["amount"]
            or 0
        )


        promoter_id = (
            withdrawal["promoter_id"]
        )


        # ==================================================
        # ALREADY REFUNDED
        # ==================================================

        if old_status in {
            "failed",
            "cancelled"
        }:

            conn.commit()

            return True


        # ==================================================
        # SUCCESSFUL CANNOT REFUND
        # ==================================================

        if old_status == "successful":

            raise ValueError(
                "Successful withdrawal cannot be refunded."
            )


        # ==================================================
        # RETURN BALANCE
        # ==================================================

        cursor.execute("""
        UPDATE promoters

        SET available_balance =
            available_balance + ?

        WHERE id=?
        """, (

            amount,
            promoter_id

        ))


        if cursor.rowcount != 1:

            raise ValueError(
                "Could not restore promoter balance."
            )


        # ==================================================
        # MARK FAILED
        # ==================================================

        cursor.execute("""
        UPDATE withdrawals

        SET

            status=?,

            transfer_status=?,

            transfer_message=?

        WHERE id=?

        AND status IN (
            'pending',
            'processing'
        )
        """, (

            transfer_status,
            transfer_status,
            transfer_message,
            withdrawal_id

        ))


        if cursor.rowcount != 1:

            raise ValueError(
                "Withdrawal could not be refunded."
            )


        conn.commit()

        return True


    except Exception:

        conn.rollback()

        raise


    finally:

        conn.close()


# ==========================================================
# UPDATE TRANSFER INFORMATION
# ==========================================================

def update_withdrawal_transfer(
    withdrawal_id,
    transfer_reference=None,
    transfer_id=None,
    transfer_status=None,
    transfer_message=None
):

    if not withdrawal_id:

        raise ValueError(
            "Withdrawal ID is required."
        )


    conn = get_connection()

    try:

        cursor = conn.cursor()


        cursor.execute("""
        UPDATE withdrawals

        SET

            transfer_reference =
                COALESCE(
                    ?,
                    transfer_reference
                ),

            transfer_id =
                COALESCE(
                    ?,
                    transfer_id
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
                )

        WHERE id=?
        """, (

            transfer_reference,
            transfer_id,
            transfer_status,
            transfer_message,
            withdrawal_id

        ))


        changed = (
            cursor.rowcount > 0
        )


        conn.commit()

        return changed


    except Exception:

        conn.rollback()

        raise


    finally:

        conn.close()


        # ==================================================
        # GET WITHDRAWAL
        # ==================================================

        cursor.execute("""
        SELECT *
        FROM withdrawals

        WHERE id=?

        LIMIT 1
        """, (withdrawal_id,))

        withdrawal = cursor.fetchone()

        if not withdrawal:

            raise ValueError(
                "Withdrawal not found."
            )

        old_status = (
            str(
                withdrawal["status"]
                or ""
            )
            .lower()
            .strip()
        )

        amount = float(
            withdrawal["amount"]
            or 0
        )

        promoter_id = (
            withdrawal["promoter_id"]
        )

        # ==================================================
        # ALREADY SUCCESSFUL
        # ==================================================

        if old_status == "successful":

            cursor.execute("""
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

                transfer_status='successful',

                transfer_message =
                    COALESCE(
                        ?,
                        transfer_message
                    )

            WHERE id=?
            """, (

                transfer_id,
                transfer_reference,
                transfer_message,
                withdrawal_id

            ))

            conn.commit()

            return True

        # ==================================================
        # ALREADY FAILED / CANCELLED
        # ==================================================

        if old_status in {
            "failed",
            "cancelled"
        }:

            raise ValueError(
                "Withdrawal has already been finalized."
            )

        # ==================================================
        # UPDATE PROMOTER
        # ==================================================

        cursor.execute("""
        UPDATE promoters

        SET withdrawn_amount =
            withdrawn_amount + ?

        WHERE id=?
        """, (
            amount,
            promoter_id
        ))

        if cursor.rowcount != 1:

            raise ValueError(
                "Could not update withdrawn amount."
            )

        # ==================================================
        # UPDATE WITHDRAWAL
        # ==================================================

        cursor.execute("""
        UPDATE withdrawals

        SET

            status='successful',

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

            transfer_status='successful',

            transfer_message =
                COALESCE(
                    ?,
                    transfer_message
                )

        WHERE id=?

        AND status IN (
            'pending',
            'processing'
        )
        """, (

            transfer_id,
            transfer_reference,
            transfer_message,
            withdrawal_id

        ))

        if cursor.rowcount != 1:

            raise ValueError(
                "Withdrawal could not be marked successful."
            )

        conn.commit()

        return True

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ==========================================================
# REFUND WITHDRAWAL
# ==========================================================
#
# Used when Flutterwave transfer fails/cancelled.
#
# Reserved amount returns to available_balance.
#
# ==========================================================

def refund_withdrawal(
    withdrawal_id,
    transfer_status="failed",
    transfer_message=None
):

    if not withdrawal_id:

        raise ValueError(
            "Withdrawal ID is required."
        )

    transfer_status = (
        transfer_status or "failed"
    ).strip().lower()

    if transfer_status not in {
        "failed",
        "cancelled"
    }:

        transfer_status = "failed"

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            "BEGIN IMMEDIATE"
        )

        # ==================================================
        # GET WITHDRAWAL
        # ==================================================

        cursor.execute("""
        SELECT *
        FROM withdrawals

        WHERE id=?

        LIMIT 1
        """, (withdrawal_id,))

        withdrawal = cursor.fetchone()

        if not withdrawal:

            raise ValueError(
                "Withdrawal not found."
            )

        old_status = (
            str(
                withdrawal["status"]
                or ""
            )
            .lower()
            .strip()
        )

        amount = float(
            withdrawal["amount"]
            or 0
        )

        promoter_id = (
            withdrawal["promoter_id"]
        )

        # ==================================================
        # ALREADY REFUNDED
        # ==================================================

        if old_status in {
            "failed",
            "cancelled"
        }:

            cursor.execute("""
            UPDATE withdrawals

            SET

                transfer_status=?,

                transfer_message =
                    COALESCE(
                        ?,
                        transfer_message
                    )

            WHERE id=?
            """, (

                transfer_status,
                transfer_message,
                withdrawal_id

            ))

            conn.commit()

            return True

        # ==================================================
        # SUCCESSFUL CANNOT REFUND
        # ==================================================

        if old_status == "successful":

            raise ValueError(
                "Successful withdrawal cannot be refunded."
            )

        # ==================================================
        # RETURN BALANCE
        # ==================================================

        cursor.execute("""
        UPDATE promoters

        SET available_balance =
            available_balance + ?

        WHERE id=?
        """, (
            amount,
            promoter_id
        ))

        if cursor.rowcount != 1:

            raise ValueError(
                "Could not restore promoter balance."
            )

        # ==================================================
        # UPDATE WITHDRAWAL
        # ==================================================

        cursor.execute("""
        UPDATE withdrawals

        SET

            status=?,

            transfer_status=?,

            transfer_message=?

        WHERE id=?

        AND status IN (
            'pending',
            'processing'
        )
        """, (

            transfer_status,
            transfer_status,
            transfer_message,
            withdrawal_id

        ))

        if cursor.rowcount != 1:

            raise ValueError(
                "Withdrawal could not be refunded."
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
    status
):

    if not withdrawal_id:

        raise ValueError(
            "Withdrawal ID is required."
        )

    status = (
        status or ""
    ).strip().lower()

    allowed_statuses = {

        "pending",
        "processing",
        "successful",
        "failed",
        "cancelled"

    }

    if status not in allowed_statuses:

        raise ValueError(
            "Invalid withdrawal status."
        )

    # ======================================================
    # SUCCESSFUL
    # ======================================================

    if status == "successful":

        return mark_withdrawal_successful(
            withdrawal_id
        )

    # ======================================================
    # FAILED / CANCELLED
    # ======================================================

    if status in {
        "failed",
        "cancelled"
    }:

        return refund_withdrawal(
            withdrawal_id,
            transfer_status=status
        )

    # ======================================================
    # PENDING / PROCESSING
    # ======================================================

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            "BEGIN IMMEDIATE"
        )

        cursor.execute("""
        SELECT status
        FROM withdrawals

        WHERE id=?

        LIMIT 1
        """, (withdrawal_id,))

        withdrawal = cursor.fetchone()

        if not withdrawal:

            raise ValueError(
                "Withdrawal not found."
            )

        old_status = (
            str(
                withdrawal["status"]
                or ""
            )
            .lower()
            .strip()
        )

        # ==================================================
        # FINAL STATUS CANNOT CHANGE
        # ==================================================

        if old_status in {
            "successful",
            "failed",
            "cancelled"
        }:

            raise ValueError(
                "Final withdrawal status cannot be changed."
            )

        # ==================================================
        # UPDATE
        # ==================================================

        cursor.execute("""
        UPDATE withdrawals

        SET status=?

        WHERE id=?

        AND status IN (
            'pending',
            'processing'
        )
        """, (
            status,
            withdrawal_id
        ))

        if cursor.rowcount != 1:

            raise ValueError(
                "Withdrawal status could not be updated."
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