# ==========================================================
# ALHIKAM LEARNING CENTER V2
# database.py
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

    return conn


# ==========================================================
# INITIALIZE
# ==========================================================

def initialize_database():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        payment_token TEXT,

        tx_ref TEXT,

        full_name TEXT,

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

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS promoters(

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

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments(

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

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS commissions(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        promoter_id INTEGER NOT NULL,

        student_id INTEGER,

        tx_ref TEXT,

        payment_amount REAL DEFAULT 0,

        commission_rate REAL DEFAULT 0,

        commission_amount REAL DEFAULT 0,

        status TEXT DEFAULT 'pending',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(promoter_id)
        REFERENCES promoters(id),

        FOREIGN KEY(student_id)
        REFERENCES students(id)

    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS withdrawals(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        promoter_id INTEGER NOT NULL,

        amount REAL DEFAULT 0,

        bank_name TEXT,

        account_name TEXT,

        account_number TEXT,

        status TEXT DEFAULT 'pending',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(promoter_id)
        REFERENCES promoters(id)

    )
    """)

    # ------------------------------------------------------
    # Indexes
    # ------------------------------------------------------

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS
    idx_students_telegram
    ON students(telegram_id)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS
    idx_students_referral
    ON students(referral_code)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS
    idx_students_tx_ref
    ON students(tx_ref)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS
    idx_promoters_referral
    ON promoters(referral_code)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS
    idx_commissions_promoter
    ON commissions(promoter_id)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS
    idx_commissions_tx_ref
    ON commissions(tx_ref)
    """)

    conn.commit()

    conn.close()


# ==========================================================
# ADD STUDENT
# ==========================================================

def add_student(data):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO students(

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

    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)

    """, (

        data.get("payment_token", ""),

        data.get("tx_ref", ""),

        data.get("full_name", ""),

        data.get("phone", ""),

        data.get("email", ""),

        data.get("course", ""),

        str(data.get("telegram_id", "")),

        data.get("telegram_username", ""),

        data.get("telegram_name", ""),

        data.get("payment_plan", ""),

        float(data.get("amount_paid", 0) or 0),

        data.get(
            "payment_status",
            "Pending"
        ),

        int(
            data.get(
                "registration_completed",
                0
            )
        ),

        data.get("referral_code", ""),

        data.get("promoter_id")

    ))

    student_id = cursor.lastrowid

    conn.commit()

    conn.close()

    return student_id


# ==========================================================
# GET STUDENT
# ==========================================================

def get_student_by_telegram_id(telegram_id):

    conn = get_connection()

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

    result = cursor.fetchone()

    conn.close()

    return result


# ==========================================================
# PROMOTER BY REFERRAL
# ==========================================================

def get_promoter_by_referral_code(referral_code):

    if not referral_code:
        return None

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM promoters
    WHERE referral_code=?
    AND status='active'
    LIMIT 1
    """, (
        referral_code.strip(),
    ))

    result = cursor.fetchone()

    conn.close()

    return result


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

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO promoters(

        full_name,
        phone,
        email,
        referral_code,
        commission_rate

    )

    VALUES(?,?,?,?,?)

    """, (

        full_name,

        phone,

        email,

        referral_code,

        commission_rate

    ))

    promoter_id = cursor.lastrowid

    conn.commit()

    conn.close()

    return promoter_id


# ==========================================================
# PROMOTER BY ID
# ==========================================================

def get_promoter_by_id(promoter_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM promoters
    WHERE id=?
    LIMIT 1
    """, (
        promoter_id,
    ))

    result = cursor.fetchone()

    conn.close()

    return result


# ==========================================================
# SAVE PAYMENT
# ==========================================================

def save_payment(data):

    tx_ref = data.get("tx_ref", "")

    if not tx_ref:
        raise ValueError(
            "tx_ref is required."
        )

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO payments(

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
        telegram_name

    )

    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)

    """, (

        tx_ref,

        data.get("transaction_id", ""),

        data.get("payment_plan", ""),

        float(data.get("amount", 0) or 0),

        data.get(
            "payment_status",
            "Pending"
        ),

        data.get("referral_code", ""),

        data.get("promoter_id"),

        data.get("promoter_name", ""),

        float(
            data.get("commission", 0) or 0
        ),

        str(
            data.get(
                "telegram_id",
                ""
            )
        ),

        data.get(
            "telegram_username",
            ""
        ),

        data.get(
            "telegram_name",
            ""
        )

    ))

    conn.commit()

    conn.close()

    return True


# ==========================================================
# GET PAYMENT
# ==========================================================

def get_payment_by_tx_ref(tx_ref):

    if not tx_ref:
        return None

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM payments
    WHERE tx_ref=?
    LIMIT 1
    """, (
        tx_ref,
    ))

    result = cursor.fetchone()

    conn.close()

    return result


# ==========================================================
# UPDATE PAYMENT STATUS
# ==========================================================

def update_payment_status(
    tx_ref,
    status,
    transaction_id=None
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    UPDATE payments

    SET

        payment_status=?,

        transaction_id=
        COALESCE(?, transaction_id)

    WHERE tx_ref=?

    """, (

        status,

        transaction_id,

        tx_ref

    ))

    conn.commit()

    conn.close()


# ==========================================================
# COMMISSION EXISTS
# ==========================================================

def commission_exists(tx_ref):

    if not tx_ref:
        return False

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT id
    FROM commissions
    WHERE tx_ref=?
    LIMIT 1
    """, (
        tx_ref,
    ))

    result = cursor.fetchone()

    conn.close()

    return result is not None


# ==========================================================
# GET COMMISSION
# ==========================================================

def get_commission_by_tx_ref(tx_ref):

    if not tx_ref:
        return None

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM commissions
    WHERE tx_ref=?
    LIMIT 1
    """, (
        tx_ref,
    ))

    result = cursor.fetchone()

    conn.close()

    return result


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

    payment_amount = float(
        payment_amount or 0
    )

    commission_amount = float(
        commission_amount or 0
    )

    if commission_amount <= 0:
        raise ValueError(
            "Commission amount must be greater than zero."
        )

    if tx_ref and commission_exists(tx_ref):

        existing = get_commission_by_tx_ref(
            tx_ref
        )

        return {

            "commission_id":
                existing["id"],

            "commission_amount":
                float(
                    existing["commission_amount"]
                )

        }

    rate = 0

    if payment_amount > 0:

        rate = (
            commission_amount /
            payment_amount
        ) * 100

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO commissions(

        promoter_id,
        student_id,
        tx_ref,
        payment_amount,
        commission_rate,
        commission_amount,
        status

    )

    VALUES(?,?,?,?,?,?,?)

    """, (

        promoter_id,

        student_id,

        tx_ref,

        payment_amount,

        rate,

        commission_amount,

        "available"

    ))

    commission_id = cursor.lastrowid

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

    """, (

        commission_amount,

        commission_amount,

        promoter_id

    ))

    conn.commit()

    conn.close()

    return {

        "commission_id":
            commission_id,

        "commission_amount":
            commission_amount

    }


# ==========================================================
# UPDATE STUDENT
# ==========================================================

def update_student(payment_token, data):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    UPDATE students

    SET

        full_name=?,
        phone=?,
        email=?,
        course=?,
        telegram_id=?,
        telegram_username=?,
        telegram_name=?,
        registration_completed=?,
        payment_status=?,
        amount_paid=?,
        referral_code=?,
        promoter_id=?,
        payment_plan=?,
        tx_ref=?

    WHERE payment_token=?

    """, (

        data.get("full_name", ""),

        data.get("phone", ""),

        data.get("email", ""),

        data.get("course", ""),

        str(data.get("telegram_id", "")),

        data.get("telegram_username", ""),

        data.get("telegram_name", ""),

        data.get(
            "registration_completed",
            0
        ),

        data.get(
            "payment_status",
            "Pending"
        ),

        float(
            data.get(
                "amount_paid",
                0
            ) or 0
        ),

        data.get("referral_code", ""),

        data.get("promoter_id"),

        data.get("payment_plan", ""),

        data.get("tx_ref", ""),

        payment_token

    ))

    conn.commit()

    conn.close()