# ==========================================================
# ALHIKAM LEARNING CENTER V2
# database.py
# ==========================================================

import sqlite3
from config import DATABASE_NAME


def get_connection():
    conn = sqlite3.connect(
        DATABASE_NAME,
        check_same_thread=False,
        timeout=30
    )
    conn.row_factory = sqlite3.Row
    return conn


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

        data.get("payment_token", ""),
        data.get("tx_ref", ""),

        data["full_name"],
        data["phone"],
        data["email"],

        data["course"],

        str(data.get("telegram_id", "")),
        data.get("telegram_username", ""),
        data.get("telegram_name", ""),

        data.get("payment_plan", ""),

        data.get("amount_paid", 0),

        data.get("payment_status", "Pending"),

        data.get("registration_completed", 0)

    ))

    conn.commit()
    conn.close()


def get_student_by_telegram_id(telegram_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM students
        WHERE telegram_id=?
        ORDER BY id DESC
        LIMIT 1
        """,
        (str(telegram_id),)
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

        registration_completed=?,

        payment_status=?,

        amount_paid=?

        WHERE payment_token=?
        """,
        (

            data["full_name"],
            data["phone"],
            data["email"],
            data["course"],

            str(data["telegram_id"]),
            data["telegram_username"],
            data["telegram_name"],

            data["registration_completed"],

            data["payment_status"],

            data["amount_paid"],

            payment_token

        )
    )

    conn.commit()
    conn.close()


def payment_completed(payment_token, amount):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE students

        SET

        payment_status='Paid',

        amount_paid=?

        WHERE payment_token=?
        """,
        (
            amount,
            payment_token
        )
    )

    conn.commit()
    conn.close()