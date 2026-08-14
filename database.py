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
# INITIALIZE DATABASE
# ==========================================================

def initialize_database():

    conn = get_connection()

    cursor = conn.cursor()


    # ======================================================
    # STUDENTS
    # ======================================================

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


    # ======================================================
    # PROMOTERS
    # ======================================================

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


    # ======================================================
    # PAYMENTS
    # ======================================================

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

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(promoter_id)
            REFERENCES promoters(id)

    )
    """)


    # ======================================================
    # COMMISSIONS
    # ======================================================

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


    # ======================================================
    # WITHDRAWALS
    # ======================================================

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


    # ======================================================
    # INDEXES
    # ======================================================

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
        idx_students_tx_ref
        ON students(tx_ref)
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
        idx_payments_tx_ref
        ON payments(tx_ref)
        """,

    ]


    for index in indexes:

        cursor.execute(index)


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

    VALUES(
        ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
    )

    """, (

        data.get(
            "payment_token",
            ""
        ),

        data.get(
            "tx_ref",
            ""
        ),

        data.get(
            "full_name",
            ""
        ),

        data.get(
            "phone",
            ""
        ),

        data.get(
            "email",
            ""
        ),

        data.get(
            "course",
            ""
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

        data.get(
            "registration_completed",
            0
        ),

        data.get(
            "referral_code",
            ""
        ),

        data.get(
            "promoter_id"
        )

    ))


    student_id = cursor.lastrowid

    conn.commit()

    conn.close()

    return student_id


# ==========================================================
# GET STUDENT BY TELEGRAM ID
# ==========================================================

def get_student_by_telegram_id(
    telegram_id
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *
        FROM students
        WHERE telegram_id=?
        ORDER BY id DESC
        LIMIT 1
    """, (

        str(
            telegram_id
        ),

    ))


    student = cursor.fetchone()

    conn.close()

    return student


# ==========================================================
# GET STUDENT BY TX REF
# ==========================================================

def get_student_by_tx_ref(
    tx_ref
):

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
    """, (

        tx_ref,

    ))


    student = cursor.fetchone()

    conn.close()

    return student


# ==========================================================
# GET PROMOTER BY REFERRAL CODE
# ==========================================================

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

        referral_code,

    ))


    promoter = cursor.fetchone()

    conn.close()

    return promoter


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
# GET PROMOTER BY ID
# ==========================================================

def get_promoter_by_id(
    promoter_id
):

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


    promoter = cursor.fetchone()

    conn.close()

    return promoter


# ==========================================================
# SAVE / UPDATE PAYMENT
# ==========================================================

def save_payment(data):

    tx_ref = (
        data.get(
            "tx_ref",
            ""
        )
        or ""
    ).strip()


    if not tx_ref:

        raise ValueError(
            "tx_ref is required."
        )


    conn = get_connection()

    cursor = conn.cursor()


    # ======================================================
    # CHECK EXISTING
    # ======================================================

    cursor.execute("""
        SELECT id
        FROM payments
        WHERE tx_ref=?
        LIMIT 1
    """, (

        tx_ref,

    ))


    existing = cursor.fetchone()


    if existing:

        cursor.execute("""
            UPDATE payments

            SET

                transaction_id=?,

                payment_plan=?,

                amount=?,

                payment_status=?,

                referral_code=?,

                promoter_id=?,

                promoter_name=?,

                commission=?

            WHERE tx_ref=?

        """, (

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

            tx_ref

        ))

    else:

        cursor.execute("""
            INSERT INTO payments(

                tx_ref,
                transaction_id,
                payment_plan,
                amount,
                payment_status,
                referral_code,
                promoter_id,
                promoter_name,
                commission

            )

            VALUES(?,?,?,?,?,?,?,?,?)

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
            )

        ))


    conn.commit()

    conn.close()

    return True


# ==========================================================
# GET PAYMENT BY TX REF
# ==========================================================

def get_payment_by_tx_ref(
    tx_ref
):

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


    payment = cursor.fetchone()

    conn.close()

    return payment


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


    conn.commit()

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

    payment_amount = float(
        payment_amount
        or 0
    )

    commission_amount = float(
        commission_amount
        or 0
    )


    if commission_amount <= 0:

        raise ValueError(
            "Commission amount must be greater than zero."
        )


    if not promoter_id:

        raise ValueError(
            "Promoter ID is required."
        )


    # ======================================================
    # DUPLICATE CHECK
    # ======================================================

    if tx_ref and commission_exists(
        tx_ref
    ):

        existing = (
            get_commission_by_tx_ref(
                tx_ref
            )
        )


        return {

            "commission_id":
                existing["id"]
                if existing
                else None,

            "commission_amount":
                existing[
                    "commission_amount"
                ]
                if existing
                else commission_amount

        }


    # ======================================================
    # COMMISSION RATE
    # ======================================================

    commission_rate = 0


    if payment_amount > 0:

        commission_rate = (

            commission_amount
            /
            payment_amount
            *
            100

        )


    conn = get_connection()

    cursor = conn.cursor()


    # ======================================================
    # INSERT COMMISSION
    # ======================================================

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

        commission_rate,

        commission_amount,

        "available"

    ))


    commission_id = cursor.lastrowid


    # ======================================================
    # UPDATE PROMOTER BALANCE
    # ======================================================

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
# COMMISSION EXISTS
# ==========================================================

def commission_exists(
    tx_ref
):

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

def get_commission_by_tx_ref(
    tx_ref
):

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
# UPDATE STUDENT
# ==========================================================

def update_student(
    payment_token,
    data
):

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

        data.get(
            "full_name",
            ""
        ),

        data.get(
            "phone",
            ""
        ),

        data.get(
            "email",
            ""
        ),

        data.get(
            "course",
            ""
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
        ),

        data.get(
            "registration_completed",
            0
        ),

        data.get(
            "payment_status",
            "Pending"
        ),

        data.get(
            "amount_paid",
            0
        ),

        data.get(
            "referral_code",
            ""
        ),

        data.get(
            "promoter_id"
        ),

        data.get(
            "payment_plan",
            ""
        ),

        data.get(
            "tx_ref",
            ""
        ),

        payment_token

    ))


    conn.commit()

    conn.close()


# ==========================================================
# PAYMENT COMPLETED
# ==========================================================

def payment_completed(
    payment_token,
    amount
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        UPDATE students

        SET

            payment_status='Paid',

            amount_paid=?

        WHERE payment_token=?

    """, (

        amount,

        payment_token

    ))


    conn.commit()

    conn.close()