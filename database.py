# ============================================================
#
# ALHIKAM LEARNING CENTER V2
# DATABASE
#
# ============================================================

import os
import sqlite3
import hashlib
import secrets


# ============================================================
# DATABASE CONFIG
# ============================================================

DATABASE_NAME = os.getenv(
    "DATABASE_NAME",
    "alhikam.db"
)

MINIMUM_WITHDRAWAL = 200
MAXIMUM_WITHDRAWAL = 5000


# ============================================================
# DATABASE CONNECTION
# ============================================================

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

    return conn


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password):

    if password is None:
        password = ""

    password = str(password)

    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        120000
    )

    return (
        "pbkdf2_sha256$120000$"
        + salt.hex()
        + "$"
        + password_hash.hex()
    )


def verify_password(password, stored_hash):

    if not password or not stored_hash:
        return False

    try:

        parts = stored_hash.split("$")

        if len(parts) != 4:
            return False

        algorithm = parts[0]
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected = bytes.fromhex(parts[3])

        if algorithm != "pbkdf2_sha256":
            return False

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            str(password).encode("utf-8"),
            salt,
            iterations
        )

        return secrets.compare_digest(
            actual,
            expected
        )

    except Exception:
        return False


# ============================================================
# WITHDRAWAL CODE
# ============================================================

def generate_withdrawal_code():

    return str(
        secrets.randbelow(900000) + 100000
    )


# ============================================================
# SAFE COLUMN MIGRATION
# ============================================================

def add_column_if_missing(
    cursor,
    table_name,
    column_name,
    column_type
):

    cursor.execute(
        f"PRAGMA table_info({table_name})"
    )

    columns = {
        row[1]
        for row in cursor.fetchall()
    }

    if column_name not in columns:

        cursor.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {column_type}
            """
        )


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database():

    conn = get_connection()
    cursor = conn.cursor()

    # ========================================================
    # PROMOTERS
    # ========================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS promoters(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        full_name TEXT NOT NULL,

        phone TEXT,

        email TEXT,

        referral_code TEXT UNIQUE NOT NULL,

        password_hash TEXT,

        withdrawal_code_hash TEXT,

        commission_rate REAL DEFAULT 20,

        total_sales INTEGER DEFAULT 0,

        total_earned REAL DEFAULT 0,

        available_balance REAL DEFAULT 0,

        withdrawn REAL DEFAULT 0,

        status TEXT DEFAULT 'active',

        created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ========================================================
    # STUDENTS
    # ========================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        payment_token TEXT,

        tx_ref TEXT UNIQUE,

        full_name TEXT,

        phone TEXT,

        email TEXT,

        course TEXT,

        faculty TEXT,

        telegram_id TEXT,

        telegram_username TEXT,

        telegram_name TEXT,

        payment_plan TEXT,

        amount_paid REAL DEFAULT 0,

        payment_status TEXT DEFAULT 'Pending',

        registration_completed INTEGER DEFAULT 0,

        referral_code TEXT,

        promoter_id INTEGER,

        created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(promoter_id)
            REFERENCES promoters(id)
    )
    """)

    # ========================================================
    # PAYMENTS
    # ========================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        tx_ref TEXT UNIQUE NOT NULL,

        transaction_id TEXT,

        amount REAL DEFAULT 0,

        currency TEXT DEFAULT 'NGN',

        payment_plan TEXT,

        payment_status TEXT DEFAULT 'Pending',

        referral_code TEXT,

        promoter_id INTEGER,

        promoter_name TEXT,

        commission REAL DEFAULT 0,

        telegram_id TEXT,

        telegram_username TEXT,

        telegram_name TEXT,

        registration_completed INTEGER DEFAULT 0,

        created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP,

        updated_at TEXT,

        FOREIGN KEY(promoter_id)
            REFERENCES promoters(id)
    )
    """)

    # ========================================================
    # COMMISSIONS
    # ========================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS commissions(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        promoter_id INTEGER NOT NULL,

        student_id INTEGER,

        tx_ref TEXT,

        payment_amount REAL DEFAULT 0,

        commission_rate REAL DEFAULT 0,

        commission_amount REAL DEFAULT 0,

        status TEXT DEFAULT 'available',

        created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(promoter_id)
            REFERENCES promoters(id),

        FOREIGN KEY(student_id)
            REFERENCES students(id)
    )
    """)

    # ========================================================
    # WITHDRAWALS
    # ========================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS withdrawals(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        promoter_id INTEGER NOT NULL,

        amount REAL DEFAULT 0,

        bank_name TEXT,

        bank_code TEXT,

        account_name TEXT,

        account_number TEXT,

        transfer_id TEXT,

        transfer_reference TEXT,

        status TEXT DEFAULT 'processing',

        message TEXT,

        created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP,

        updated_at TEXT,

        FOREIGN KEY(promoter_id)
            REFERENCES promoters(id)
    )
    """)

    # ========================================================
    # STUDENT ACTIVITY
    # ========================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_activity(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        student_id INTEGER,

        tx_ref TEXT,

        activity_type TEXT NOT NULL,

        activity_title TEXT,

        activity_description TEXT,

        metadata TEXT,

        created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(student_id)
            REFERENCES students(id)
            ON DELETE SET NULL
    )
    """)

    # ========================================================
    # SAFE MIGRATIONS
    # ========================================================

    student_columns = {
        "faculty": "TEXT",
        "course": "TEXT",
        "referral_code": "TEXT",
        "promoter_id": "INTEGER",
    }

    for column, column_type in student_columns.items():

        add_column_if_missing(
            cursor,
            "students",
            column,
            column_type
        )

    payment_columns = {
        "currency": "TEXT DEFAULT 'NGN'",
        "promoter_name": "TEXT",
        "commission": "REAL DEFAULT 0",
        "telegram_id": "TEXT",
        "telegram_username": "TEXT",
        "telegram_name": "TEXT",
        "registration_completed": "INTEGER DEFAULT 0",
        "updated_at": "TEXT",
    }

    for column, column_type in payment_columns.items():

        add_column_if_missing(
            cursor,
            "payments",
            column,
            column_type
        )

    promoter_columns = {
        "password_hash": "TEXT",
        "withdrawal_code_hash": "TEXT",
        "available_balance": "REAL DEFAULT 0",
        "total_earned": "REAL DEFAULT 0",
        "withdrawn": "REAL DEFAULT 0",
        "status": "TEXT DEFAULT 'active'",
    }

    for column, column_type in promoter_columns.items():

        add_column_if_missing(
            cursor,
            "promoters",
            column,
            column_type
        )

    withdrawal_columns = {
        "bank_code": "TEXT",
        "transfer_id": "TEXT",
        "transfer_reference": "TEXT",
        "message": "TEXT",
        "updated_at": "TEXT",
    }

    for column, column_type in withdrawal_columns.items():

        add_column_if_missing(
            cursor,
            "withdrawals",
            column,
            column_type
        )

    # ========================================================
    # INDEXES
    # ========================================================

    indexes = [

        (
            "idx_students_telegram",
            "students(telegram_id)"
        ),

        (
            "idx_students_referral",
            "students(referral_code)"
        ),

        (
            "idx_students_tx_ref",
            "students(tx_ref)"
        ),

        (
            "idx_students_phone",
            "students(phone)"
        ),

        (
            "idx_students_email",
            "students(email)"
        ),

        (
            "idx_students_created",
            "students(created_at)"
        ),

        (
            "idx_promoters_referral",
            "promoters(referral_code)"
        ),

        (
            "idx_commissions_promoter",
            "commissions(promoter_id)"
        ),

        (
            "idx_commissions_tx_ref",
            "commissions(tx_ref)"
        ),

        (
            "idx_withdrawals_promoter",
            "withdrawals(promoter_id)"
        ),

        (
            "idx_student_activity_student",
            "student_activity(student_id)"
        ),

        (
            "idx_student_activity_tx_ref",
            "student_activity(tx_ref)"
        ),

        (
            "idx_student_activity_created",
            "student_activity(created_at)"
        ),
    ]

    for name, target in indexes:

        cursor.execute(
            f"""
            CREATE INDEX IF NOT EXISTS
            {name}
            ON {target}
            """
        )

    conn.commit()
    conn.close()


# ============================================================
# STUDENT ACTIVITY
# ============================================================

def add_student_activity(
    student_id=None,
    tx_ref=None,
    activity_type="general",
    activity_title="Activity",
    activity_description="",
    metadata=None
):

    conn = get_connection()
    cursor = conn.cursor()

    if metadata is not None:
        import json

        try:
            metadata = json.dumps(
                metadata,
                ensure_ascii=False
            )
        except Exception:
            metadata = str(metadata)

    cursor.execute("""
    INSERT INTO student_activity(
        student_id,
        tx_ref,
        activity_type,
        activity_title,
        activity_description,
        metadata
    )
    VALUES(?,?,?,?,?,?)
    """, (
        student_id,
        tx_ref,
        activity_type,
        activity_title,
        activity_description,
        metadata
    ))

    activity_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return activity_id


def get_student_activity(student_id):

    if not student_id:
        return []

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM student_activity
    WHERE student_id=?
    ORDER BY id DESC
    """, (student_id,))

    result = cursor.fetchall()

    conn.close()

    return result


def get_student_activity_by_tx_ref(tx_ref):

    if not tx_ref:
        return []

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM student_activity
    WHERE tx_ref=?
    ORDER BY id DESC
    """, (tx_ref,))

    result = cursor.fetchall()

    conn.close()

    return result


# ============================================================
# ADD STUDENT
# ============================================================

def add_student(data, *args):

    if not isinstance(data, dict):

        data = {
            "payment_token": data,
            "tx_ref": args[0] if len(args) > 0 else "",
            "full_name": args[1] if len(args) > 1 else "",
            "phone": args[2] if len(args) > 2 else "",
            "email": args[3] if len(args) > 3 else "",
        }

    tx_ref = (
        data.get("tx_ref")
        or ""
    ).strip()

    conn = get_connection()
    cursor = conn.cursor()

    # ========================================================
    # EXISTING STUDENT
    # ========================================================

    existing = None

    if tx_ref:

        cursor.execute("""
        SELECT id
        FROM students
        WHERE tx_ref=?
        LIMIT 1
        """, (tx_ref,))

        existing = cursor.fetchone()

    if existing:

        student_id = existing["id"]

        cursor.execute("""
        UPDATE students
        SET payment_token=?,
            full_name=?,
            phone=?,
            email=?,
            course=?,
            faculty=?,
            telegram_id=?,
            telegram_username=?,
            telegram_name=?,
            payment_plan=?,
            amount_paid=?,
            payment_status=?,
            registration_completed=?,
            referral_code=?,
            promoter_id=?
        WHERE id=?
        """, (
            data.get("payment_token", ""),
            data.get("full_name", ""),
            data.get("phone", ""),
            data.get("email", ""),
            data.get("course", ""),
            data.get("faculty", ""),
            str(data.get("telegram_id", "") or ""),
            data.get("telegram_username", ""),
            data.get("telegram_name", ""),
            data.get("payment_plan", ""),
            float(data.get("amount_paid", 0) or 0),
            data.get("payment_status", "Pending"),
            int(data.get("registration_completed", 0) or 0),
            data.get("referral_code", ""),
            data.get("promoter_id"),
            student_id
        ))

        conn.commit()
        conn.close()

        return student_id

    # ========================================================
    # NEW STUDENT
    # ========================================================

    cursor.execute("""
    INSERT INTO students(

        payment_token,
        tx_ref,
        full_name,
        phone,
        email,
        course,
        faculty,
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
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data.get("payment_token", ""),
        tx_ref,
        data.get("full_name", ""),
        data.get("phone", ""),
        data.get("email", ""),
        data.get("course", ""),
        data.get("faculty", ""),
        str(data.get("telegram_id", "") or ""),
        data.get("telegram_username", ""),
        data.get("telegram_name", ""),
        data.get("payment_plan", ""),
        float(data.get("amount_paid", 0) or 0),
        data.get("payment_status", "Pending"),
        int(data.get("registration_completed", 0) or 0),
        data.get("referral_code", ""),
        data.get("promoter_id"),
    ))

    student_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return student_id


# ============================================================
# CREATE OR GET STUDENT
# ============================================================

def create_or_get_student(data):

    tx_ref = (
        data.get("tx_ref")
        or ""
    ).strip()

    if tx_ref:

        existing = get_student_by_tx_ref(
            tx_ref
        )

        if existing:
            return existing

    student_id = add_student(data)

    return get_student_by_id(
        student_id
    )


# ============================================================
# GET STUDENT BY ID
# ============================================================

def get_student_by_id(student_id):

    if not student_id:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM students
    WHERE id=?
    LIMIT 1
    """, (student_id,))

    result = cursor.fetchone()

    conn.close()

    return result


# ============================================================
# GET STUDENT BY TX REF
# ============================================================

def get_student_by_tx_ref(tx_ref):

    if not tx_ref:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM students
    WHERE tx_ref=?
    ORDER BY id DESC
    LIMIT 1
    """, (tx_ref,))

    result = cursor.fetchone()

    conn.close()

    return result


# ============================================================
# GET STUDENT BY TELEGRAM ID
# ============================================================

def get_student_by_telegram_id(telegram_id):

    if not telegram_id:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM students
    WHERE telegram_id=?
    ORDER BY id DESC
    LIMIT 1
    """, (str(telegram_id),))

    result = cursor.fetchone()

    conn.close()

    return result


# ============================================================
# GET ALL STUDENTS
# ============================================================

def get_all_students():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        students.*,
        promoters.full_name AS promoter_name
    FROM students
    LEFT JOIN promoters
        ON promoters.id = students.promoter_id
    ORDER BY students.id DESC
    """)

    result = cursor.fetchall()

    conn.close()

    return result


# ============================================================
# SEARCH STUDENTS
# ============================================================

def search_students(search=""):

    search = str(
        search or ""
    ).strip()

    conn = get_connection()
    cursor = conn.cursor()

    if not search:

        cursor.execute("""
        SELECT
            students.*,
            promoters.full_name AS promoter_name
        FROM students
        LEFT JOIN promoters
            ON promoters.id = students.promoter_id
        ORDER BY students.id DESC
        """)

    else:

        pattern = f"%{search}%"

        cursor.execute("""
        SELECT
            students.*,
            promoters.full_name AS promoter_name
        FROM students
        LEFT JOIN promoters
            ON promoters.id = students.promoter_id
        WHERE
            students.full_name LIKE ?
            OR students.phone LIKE ?
            OR students.email LIKE ?
            OR students.telegram_id LIKE ?
            OR students.telegram_username LIKE ?
            OR students.tx_ref LIKE ?
            OR students.referral_code LIKE ?
        ORDER BY students.id DESC
        """, (
            pattern,
            pattern,
            pattern,
            pattern,
            pattern,
            pattern,
            pattern,
        ))

    result = cursor.fetchall()

    conn.close()

    return result


# ============================================================
# UPDATE STUDENT
# ============================================================

def update_student(payment_token, data):

    if not payment_token:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE students
    SET full_name=?,
        phone=?,
        email=?,
        course=?,
        faculty=?,
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
        data.get("faculty", ""),
        str(data.get("telegram_id", "") or ""),
        data.get("telegram_username", ""),
        data.get("telegram_name", ""),
        int(data.get("registration_completed", 0) or 0),
        data.get("payment_status", "Pending"),
        float(data.get("amount_paid", 0) or 0),
        data.get("referral_code", ""),
        data.get("promoter_id"),
        data.get("payment_plan", ""),
        data.get("tx_ref", ""),
        payment_token
    ))

    changed = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return changed


# ============================================================
# UPDATE STUDENT FACULTY
# ============================================================

def update_student_faculty(tx_ref, faculty):

    if not tx_ref:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE students
    SET faculty=?,
        course=?
    WHERE tx_ref=?
    """, (
        faculty,
        faculty,
        tx_ref
    ))

    changed = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return changed


# ============================================================
# MARK REGISTRATION COMPLETED
# ============================================================

def mark_payment_registration_completed(tx_ref):

    if not tx_ref:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE students
    SET registration_completed=1,
        payment_status='Successful'
    WHERE tx_ref=?
    """, (tx_ref,))

    student = get_student_by_tx_ref(
        tx_ref
    )

    cursor.execute("""
    UPDATE payments
    SET registration_completed=1
    WHERE tx_ref=?
    """, (tx_ref,))

    changed = cursor.rowcount > 0

    conn.commit()
    conn.close()

    if student:

        add_student_activity(
            student_id=student["id"],
            tx_ref=tx_ref,
            activity_type="registration_completed",
            activity_title="Registration Completed",
            activity_description=(
                "Student completed registration."
            )
        )

    return changed


def payment_registration_completed(tx_ref):

    payment = get_payment_by_tx_ref(
        tx_ref
    )

    if not payment:
        return False

    try:

        return int(
            payment["registration_completed"]
            or 0
        ) == 1

    except Exception:

        return False


# ============================================================
# PAYMENT
# ============================================================

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
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO payments(

        tx_ref,
        transaction_id,
        amount,
        currency,
        payment_plan,
        payment_status,
        referral_code,
        promoter_id,
        promoter_name,
        commission,
        telegram_id,
        telegram_username,
        telegram_name,
        registration_completed,
        created_at,
        updated_at

    )
    VALUES(
        ?,?,?,?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP
    )
    """, (
        tx_ref,
        data.get("transaction_id", ""),
        float(data.get("amount", 0) or 0),
        data.get("currency", "NGN"),
        data.get("payment_plan", ""),
        data.get("payment_status", "Pending"),
        data.get("referral_code", ""),
        data.get("promoter_id"),
        data.get("promoter_name", ""),
        float(data.get("commission", 0) or 0),
        str(data.get("telegram_id", "") or ""),
        data.get("telegram_username", ""),
        data.get("telegram_name", ""),
        int(data.get("registration_completed", 0) or 0),
    ))

    conn.commit()
    conn.close()

    return True


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
    """, (tx_ref,))

    result = cursor.fetchone()

    conn.close()

    return result


def update_payment_status(
    tx_ref,
    status,
    transaction_id=None
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE payments
    SET payment_status=?,
        transaction_id=COALESCE(
            ?,
            transaction_id
        ),
        updated_at=CURRENT_TIMESTAMP
    WHERE tx_ref=?
    """, (
        status,
        transaction_id,
        tx_ref
    ))

    conn.commit()
    conn.close()

    # ========================================================
    # ACTIVITY
    # ========================================================

    student = get_student_by_tx_ref(
        tx_ref
    )

    if student:

        normalized = str(
            status or ""
        ).lower()

        if normalized in (
            "successful",
            "success",
            "completed"
        ):

            add_student_activity(
                student_id=student["id"],
                tx_ref=tx_ref,
                activity_type="payment_successful",
                activity_title="Payment Successful",
                activity_description=(
                    "Student payment was successfully verified."
                )
            )

        else:

            add_student_activity(
                student_id=student["id"],
                tx_ref=tx_ref,
                activity_type="payment_status",
                activity_title="Payment Status Updated",
                activity_description=(
                    f"Payment status: {status}"
                )
            )


# ============================================================
# PROMOTER
# ============================================================

def _generate_unique_referral_code():

    while True:

        code = (
            "ALC"
            + secrets.token_hex(4).upper()
        )

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT id
        FROM promoters
        WHERE referral_code=?
        LIMIT 1
        """, (code,))

        exists = cursor.fetchone()

        conn.close()

        if not exists:
            return code


def add_promoter(
    full_name,
    phone,
    email,
    commission_rate=20,
    referral_code=None
):

    if not referral_code:

        referral_code = (
            _generate_unique_referral_code()
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO promoters(
        full_name,
        phone,
        email,
        referral_code,
        commission_rate,
        status
    )
    VALUES(?,?,?,?,?,?)
    """, (
        full_name,
        phone,
        email,
        referral_code.strip(),
        float(commission_rate or 20),
        "active"
    ))

    promoter_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "id": promoter_id,
        "full_name": full_name,
        "phone": phone,
        "email": email,
        "referral_code": referral_code,
        "commission_rate": float(
            commission_rate or 20
        )
    }


def get_promoter_by_id(promoter_id):

    if not promoter_id:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM promoters
    WHERE id=?
    LIMIT 1
    """, (promoter_id,))

    result = cursor.fetchone()

    conn.close()

    return result


def get_promoter_by_referral_code(
    referral_code
):

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


def get_all_promoters():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM promoters
    ORDER BY id DESC
    """)

    result = cursor.fetchall()

    conn.close()

    return result


def set_promoter_password(
    promoter_id,
    password
):

    if not promoter_id:
        return False

    password_hash = hash_password(
        password
    )

    withdrawal_code = (
        generate_withdrawal_code()
    )

    withdrawal_code_hash = hash_password(
        withdrawal_code
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE promoters
    SET password_hash=?,
        withdrawal_code_hash=?
    WHERE id=?
    """, (
        password_hash,
        withdrawal_code_hash,
        promoter_id
    ))

    changed = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return withdrawal_code if changed else None


def verify_promoter_password(
    promoter_id,
    password
):

    promoter = get_promoter_by_id(
        promoter_id
    )

    if not promoter:
        return False

    return verify_password(
        password,
        promoter["password_hash"]
    )


def verify_promoter_withdrawal_code(
    promoter_id,
    code
):

    promoter = get_promoter_by_id(
        promoter_id
    )

    if not promoter:
        return False

    return verify_password(
        code,
        promoter["withdrawal_code_hash"]
    )


# ============================================================
# COMMISSIONS
# ============================================================

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
    """, (tx_ref,))

    result = cursor.fetchone()

    conn.close()

    return result is not None


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
    """, (tx_ref,))

    result = cursor.fetchone()

    conn.close()

    return result


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

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            "BEGIN IMMEDIATE"
        )

        cursor.execute("""
        SELECT id, commission_amount
        FROM commissions
        WHERE tx_ref=?
        LIMIT 1
        """, (tx_ref,))

        existing = cursor.fetchone()

        if existing:

            conn.rollback()

            return {
                "commission_id":
                    existing["id"],

                "commission_amount":
                    float(
                        existing[
                            "commission_amount"
                        ] or 0
                    )
            }

        rate = (
            (
                commission_amount
                / payment_amount
            ) * 100
            if payment_amount > 0
            else 0
        )

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
        SET total_sales=
                COALESCE(total_sales,0)+1,

            total_earned=
                COALESCE(total_earned,0)+?,

            available_balance=
                COALESCE(available_balance,0)+?

        WHERE id=?
        """, (
            commission_amount,
            commission_amount,
            promoter_id
        ))

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


# ============================================================
# WITHDRAWAL
# ============================================================

def create_withdrawal(
    promoter_id,
    amount,
    bank_name,
    bank_code,
    account_name,
    account_number
):

    try:

        amount = float(
            amount or 0
        )

    except Exception:

        raise ValueError(
            "Invalid withdrawal amount."
        )

    account_number = str(
        account_number or ""
    ).strip()

    bank_code = str(
        bank_code or ""
    ).strip()

    # ========================================================
    # MINIMUM WITHDRAWAL
    # ========================================================

    if amount < MINIMUM_WITHDRAWAL:

        raise ValueError(
            "Minimum withdrawal is ₦200."
        )

    # ========================================================
    # MAXIMUM WITHDRAWAL
    # ========================================================

    if amount > MAXIMUM_WITHDRAWAL:

        raise ValueError(
            "Maximum withdrawal is ₦5,000."
        )

    # ========================================================
    # ACCOUNT NUMBER
    # ========================================================

    if (
        len(account_number) != 10
        or not account_number.isdigit()
    ):

        raise ValueError(
            "Account number must contain 10 digits."
        )

    # ========================================================
    # BANK CODE
    # ========================================================

    if not bank_code:

        raise ValueError(
            "Bank code is required."
        )

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            "BEGIN IMMEDIATE"
        )

        cursor.execute("""
        SELECT *
        FROM promoters
        WHERE id=?
        LIMIT 1
        """, (promoter_id,))

        promoter = cursor.fetchone()

        if not promoter:

            raise ValueError(
                "Promoter not found."
            )

        # ====================================================
        # PROMOTER STATUS
        # ====================================================

        if (
            str(
                promoter["status"] or ""
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

        # ====================================================
        # AVAILABLE BALANCE
        # ====================================================

        if amount > balance:

            raise ValueError(
                "Insufficient available balance."
            )

        # ====================================================
        # EXISTING PROCESSING WITHDRAWAL
        # ====================================================

        cursor.execute("""
        SELECT id
        FROM withdrawals
        WHERE promoter_id=?
        AND status='processing'
        LIMIT 1
        """, (promoter_id,))

        if cursor.fetchone():

            raise ValueError(
                "You already have a withdrawal being processed."
            )

        # ====================================================
        # CREATE WITHDRAWAL
        # ====================================================

        cursor.execute("""
        INSERT INTO withdrawals(

            promoter_id,
            amount,
            bank_name,
            bank_code,
            account_name,
            account_number,
            status

        )
        VALUES(?,?,?,?,?,?,?)
        """, (
            promoter_id,
            amount,
            bank_name,
            bank_code,
            account_name,
            account_number,
            "processing"
        ))

        withdrawal_id = cursor.lastrowid

        # ====================================================
        # RESERVE BALANCE
        # ====================================================

        cursor.execute("""
        UPDATE promoters
        SET available_balance=
            available_balance-?
        WHERE id=?
        """, (
            amount,
            promoter_id
        ))

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

    if not withdrawal_id:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        withdrawals.*,
        promoters.full_name AS promoter_name
    FROM withdrawals
    LEFT JOIN promoters
        ON promoters.id=withdrawals.promoter_id
    WHERE withdrawals.id=?
    LIMIT 1
    """, (withdrawal_id,))

    result = cursor.fetchone()

    conn.close()

    return result


def get_all_withdrawals():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        withdrawals.*,
        promoters.full_name AS promoter_name
    FROM withdrawals
    LEFT JOIN promoters
        ON promoters.id=withdrawals.promoter_id
    ORDER BY withdrawals.id DESC
    """)

    result = cursor.fetchall()

    conn.close()

    return result


def get_withdrawals_by_promoter(
    promoter_id
):

    if not promoter_id:
        return []

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM withdrawals
    WHERE promoter_id=?
    ORDER BY id DESC
    """, (promoter_id,))

    result = cursor.fetchall()

    conn.close()

    return result


def get_promoter_withdrawals(
    promoter_id
):

    return get_withdrawals_by_promoter(
        promoter_id
    )


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

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE withdrawals
    SET transfer_id=COALESCE(
            ?,
            transfer_id
        ),

        transfer_reference=COALESCE(
            ?,
            transfer_reference
        ),

        status=COALESCE(
            ?,
            status
        ),

        message=COALESCE(
            ?,
            message
        ),

        updated_at=CURRENT_TIMESTAMP

    WHERE id=?
    """, (
        transfer_id,
        transfer_reference,
        status,
        message,
        withdrawal_id
    ))

    changed = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return changed


# ============================================================
# UPDATE WITHDRAWAL STATUS
# ============================================================

def update_withdrawal_status(
    withdrawal_id,
    status,
    message=None
):

    status = str(
        status or ""
    ).lower().strip()

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            "BEGIN IMMEDIATE"
        )

        cursor.execute("""
        SELECT *
        FROM withdrawals
        WHERE id=?
        LIMIT 1
        """, (withdrawal_id,))

        withdrawal = cursor.fetchone()

        if not withdrawal:

            conn.rollback()
            return False

        old_status = str(
            withdrawal["status"]
            or ""
        ).lower()

        amount = float(
            withdrawal["amount"]
            or 0
        )

        promoter_id = withdrawal[
            "promoter_id"
        ]

        # ====================================================
        # FAILED / CANCELLED
        # ====================================================

        if (
            status in (
                "failed",
                "cancelled",
                "canceled"
            )
            and old_status
            not in (
                "failed",
                "cancelled",
                "canceled"
            )
        ):

            cursor.execute("""
            UPDATE promoters
            SET available_balance=
                available_balance+?
            WHERE id=?
            """, (
                amount,
                promoter_id
            ))

        # ====================================================
        # SUCCESSFUL
        # ====================================================

        if (
            status in (
                "successful",
                "success",
                "completed",
                "complete"
            )
            and old_status
            not in (
                "successful",
                "success",
                "completed",
                "complete"
            )
        ):

            cursor.execute("""
            UPDATE promoters
            SET withdrawn=
                COALESCE(withdrawn,0)+?
            WHERE id=?
            """, (
                amount,
                promoter_id
            ))

        cursor.execute("""
        UPDATE withdrawals
        SET status=?,
            message=COALESCE(
                ?,
                message
            ),
            updated_at=CURRENT_TIMESTAMP
        WHERE id=?
        """, (
            status,
            message,
            withdrawal_id
        ))

        conn.commit()

        return True

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ============================================================
# PROCESS TRANSFER RESULT
# ============================================================

def process_transfer_result(
    withdrawal_id,
    status,
    message=None,
    transfer_id=None,
    transfer_reference=None
):

    update_withdrawal_transfer(
        withdrawal_id=withdrawal_id,
        transfer_id=transfer_id,
        transfer_reference=transfer_reference,
        status=status,
        message=message
    )

    if str(status).lower() in (
        "successful",
        "success",
        "completed",
        "complete",
        "failed",
        "cancelled",
        "canceled"
    ):

        return update_withdrawal_status(
            withdrawal_id=withdrawal_id,
            status=status,
            message=message
        )

    return True


# ============================================================
# MARK WITHDRAWAL SUCCESSFUL
# ============================================================

def mark_withdrawal_successful(
    withdrawal_id,
    transfer_id=None,
    transfer_reference=None
):

    update_withdrawal_transfer(
        withdrawal_id=withdrawal_id,
        transfer_id=transfer_id,
        transfer_reference=transfer_reference,
        status="successful"
    )

    return update_withdrawal_status(
        withdrawal_id=withdrawal_id,
        status="successful"
    )


# ============================================================
# REFUND WITHDRAWAL
# ============================================================

def refund_withdrawal(
    withdrawal_id
):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            "BEGIN IMMEDIATE"
        )

        cursor.execute("""
        SELECT *
        FROM withdrawals
        WHERE id=?
        LIMIT 1
        """, (withdrawal_id,))

        withdrawal = cursor.fetchone()

        if not withdrawal:

            conn.rollback()
            return False

        if str(
            withdrawal["status"] or ""
        ).lower() != "processing":

            conn.rollback()
            return False

        amount = float(
            withdrawal["amount"]
            or 0
        )

        promoter_id = withdrawal[
            "promoter_id"
        ]

        cursor.execute("""
        UPDATE promoters
        SET available_balance=
            available_balance+?
        WHERE id=?
        """, (
            amount,
            promoter_id
        ))

        cursor.execute("""
        UPDATE withdrawals
        SET status='failed',
            updated_at=CURRENT_TIMESTAMP
        WHERE id=?
        AND status='processing'
        """, (withdrawal_id,))

        conn.commit()

        return True

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ============================================================
# INITIALIZE
# ============================================================

initialize_database()