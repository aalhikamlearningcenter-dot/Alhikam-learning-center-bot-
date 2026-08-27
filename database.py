# ==========================================================
# ALHIKAM LEARNING CENTER V2
# database.py
#
# PAYMENT
# REFERRAL
# COMMISSION
# REGISTRATION
# WITHDRAWAL
# ==========================================================

import sqlite3

from config import DATABASE_NAME

==========================================================

import sqlite3

from config import DATABASE_NAME

==========================================================

CONNECTION

==========================================================

def get_connection():

conn = sqlite3.connect(  
    DATABASE_NAME,  
    check_same_thread=False,  
    timeout=30  
)  

conn.row_factory = sqlite3.Row  

conn.execute("PRAGMA foreign_keys = ON")  
conn.execute("PRAGMA busy_timeout = 30000")  

return conn

==========================================================

INITIALIZE DATABASE

==========================================================

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

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
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

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  

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

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  

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

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  

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

        account_name TEXT NOT NULL,  

        account_number TEXT NOT NULL,  

        status TEXT DEFAULT 'pending',  

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  

        FOREIGN KEY (promoter_id)  
            REFERENCES promoters(id)  
    )  
    """)  

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

==========================================================

STUDENT

==========================================================

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

        data.get(  
            "promoter_id"  
        )  

    ))  

    student_id = cursor.lastrowid  

    conn.commit()  

    return student_id  

except Exception:  

    conn.rollback()  
    raise  

finally:  

    conn.close()

==========================================================

GET STUDENT BY ID

==========================================================

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
    """, (  
        student_id,  
    ))  

    return cursor.fetchone()  

finally:  

    conn.close()

==========================================================

GET STUDENT BY TELEGRAM ID

==========================================================

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

==========================================================

GET STUDENT BY TX REF

==========================================================

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
    """, (  
        tx_ref,  
    ))  

    return cursor.fetchone()  

finally:  

    conn.close()

==========================================================

PROMOTER

==========================================================

def get_promoter_by_referral_code(referral_code):

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

==========================================================

GET PROMOTER BY ID

==========================================================

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
    """, (  
        promoter_id,  
    ))  

    return cursor.fetchone()  

finally:  

    conn.close()

==========================================================

ADD PROMOTER

==========================================================

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

==========================================================

PAYMENT

==========================================================

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
    SELECT  
        registration_completed  
    FROM payments  
    WHERE tx_ref=?  
    LIMIT 1  
    """, (  
        tx_ref,  
    ))  

    existing = cursor.fetchone()  

    if existing:  

        registration_completed = int(  
            existing[  
                "registration_completed"  
            ]  
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

==========================================================

GET PAYMENT

==========================================================

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
    """, (  
        tx_ref,  
    ))  

    return cursor.fetchone()  

finally:  

    conn.close()

==========================================================

UPDATE PAYMENT STATUS

==========================================================

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
            COALESCE(?, transaction_id)  

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

==========================================================

MARK REGISTRATION COMPLETED

==========================================================

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
    """, (  
        tx_ref,  
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

==========================================================

COMMISSION EXISTS

==========================================================

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
    """, (  
        tx_ref,  
    ))  

    return (  
        cursor.fetchone()  
        is not None  
    )  

finally:  

    conn.close()

==========================================================

GET COMMISSION

==========================================================

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
    """, (  
        tx_ref,  
    ))  

    return cursor.fetchone()  

finally:  

    conn.close()

==========================================================

CREATE COMMISSION

==========================================================

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
    """, (  
        tx_ref,  
    ))  

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
    """, (  
        promoter_id,  
    ))  

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

    commission_id = (  
        cursor.lastrowid  
    )  

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

==========================================================

LINK COMMISSION TO STUDENT

==========================================================

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

==========================================================

CREATE WITHDRAWAL

==========================================================

def create_withdrawal(
promoter_id,
amount,
bank_name,
account_name,
account_number
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

if amount < 5000:  

    raise ValueError(  
        "Minimum withdrawal is ₦5,000."  
    )  

bank_name = (  
    bank_name or ""  
).strip()  

account_name = (  
    account_name or ""  
).strip()  

account_number = (  
    account_number or ""  
).strip()  

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

    # --------------------------------------------------  
    # PROMOTER  
    # --------------------------------------------------  

    cursor.execute("""  
    SELECT  
        id,  
        available_balance,  
        status  

    FROM promoters  

    WHERE id=?  

    LIMIT 1  
    """, (  
        promoter_id,  
    ))  

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

    # --------------------------------------------------  
    # RESERVE BALANCE  
    # --------------------------------------------------  

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

    # --------------------------------------------------  
    # CREATE WITHDRAWAL  
    # --------------------------------------------------  

    cursor.execute("""  
    INSERT INTO withdrawals (  

        promoter_id,  
        amount,  

        bank_name,  
        account_name,  
        account_number,  

        status  

    )  
    VALUES (?, ?, ?, ?, ?, ?)  
    """, (  

        promoter_id,  
        amount,  

        bank_name,  
        account_name,  
        account_number,  

        "pending"  

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

==========================================================

GET WITHDRAWAL

==========================================================

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
    """, (  
        withdrawal_id,  
    ))  

    return cursor.fetchone()  

finally:  

    conn.close()

==========================================================

GET PROMOTER WITHDRAWALS

==========================================================

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
    """, (  
        promoter_id,  
    ))  

    return cursor.fetchall()  

finally:  

    conn.close()

==========================================================

UPDATE WITHDRAWAL STATUS

==========================================================

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

conn = get_connection()  

try:  

    cursor = conn.cursor()  

    cursor.execute(  
        "BEGIN IMMEDIATE"  
    )  

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

    old_status = (  
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

    # --------------------------------------------------  
    # SAME STATUS  
    # --------------------------------------------------  

    if old_status == status:  

        conn.commit()  
        return True  

    # --------------------------------------------------  
    # FINAL STATUS  
    # --------------------------------------------------  

    if old_status in {  

        "successful",  
        "failed",  
        "cancelled"  

    }:  

        raise ValueError(  
            "Final withdrawal status cannot be changed."  
        )  

    # --------------------------------------------------  
    # SUCCESSFUL  
    # --------------------------------------------------  

    if status == "successful":  

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

    # --------------------------------------------------  
    # FAILED / CANCELLED  
    # --------------------------------------------------  

    elif status in {  

        "failed",  
        "cancelled"  

    }:  

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

    # --------------------------------------------------  
    # UPDATE STATUS  
    # --------------------------------------------------  

    cursor.execute("""  
    UPDATE withdrawals  

    SET status=?  

    WHERE id=?  

    AND status=?  
    """, (  

        status,  
        withdrawal_id,  
        old_status  

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

==========================================================

START DATABASE

==========================================================

initialize_database()