import sqlite3

DATABASE_NAME = "alhikam.db"


def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        payment_token TEXT UNIQUE,

        tx_ref TEXT UNIQUE,

        full_name TEXT,

        phone TEXT,

        email TEXT,

        course TEXT,

        telegram_id TEXT,

        telegram_username TEXT,

        telegram_name TEXT,

        payment_plan TEXT,

        amount_paid REAL,

        payment_status TEXT,

        registration_completed INTEGER DEFAULT 0,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    conn.commit()
    conn.close()


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

        registration_completed

    )

    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)

    """, (

        data["payment_token"],

        data["tx_ref"],

        data["full_name"],

        data["phone"],

        data["email"],

        data["course"],

        data.get("telegram_id"),

        data.get("telegram_username"),

        data.get("telegram_name"),

        data["payment_plan"],

        data["amount_paid"],

        data["payment_status"],

        data["registration_completed"]

    ))

    conn.commit()

    conn.close()


def get_student(payment_token):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(

        "SELECT * FROM students WHERE payment_token=?",

        (payment_token,)

    )

    student = cursor.fetchone()

    conn.close()

    return student

def update_student(payment_token, data):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE students
        SET
            full_name=?,
            phone=?,
            email=?,
            course=?,
            telegram_id=?,
            telegram_username=?,
            telegram_name=?,
            registration_completed=?
        WHERE payment_token=?
        """,
        (
            data["full_name"],
            data["phone"],
            data["email"],
            data["course"],
            data.get("telegram_id"),
            data.get("telegram_username"),
            data.get("telegram_name"),
            1,
            payment_token,
        ),
    )

    conn.commit()
    conn.close()