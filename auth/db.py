import os
import time
import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
import json
from pathlib import Path

DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "Oscar+400"
DB_NAME = "smartlend"


def get_conn(retries=5, delay=0.3):
    last_exc = None
    for _ in range(retries):
        try:
            return mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                autocommit=True,
                charset="utf8mb4"
            )
        except mysql.connector.Error as e:
            last_exc = e
            if e.errno == errorcode.ER_BAD_DB_ERROR:
                tmp = mysql.connector.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASSWORD
                )
                cur = tmp.cursor()
                cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
                tmp.commit()
                cur.close()
                tmp.close()
            time.sleep(delay)
    raise last_exc


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    #USERS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(512),
            salt VARCHAR(64),
            role VARCHAR(32) DEFAULT 'applicant',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME NULL,
            reset_token VARCHAR(255) NULL,
            reset_expires_at DATETIME NULL
        );
    """)

    #SUBMISSIONS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            inputs TEXT,
            prediction_result VARCHAR(255),
            uploaded_file_path TEXT,
            status VARCHAR(32) DEFAULT 'submitted',
            admin_note TEXT NULL,
            reviewed_by INT NULL,
            reviewed_at DATETIME NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    try:
        cur.execute("""
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA=%s AND TABLE_NAME='submissions' AND COLUMN_NAME='confidence'
        """, (DB_NAME,))
        row = cur.fetchone()
        if row and row[0] == 0:
            cur.execute("ALTER TABLE submissions ADD COLUMN confidence DOUBLE NULL")
    except Exception:
        pass

    cur.close()
    conn.close()


try:
    init_db()
except Exception:
    pass


#USERS
def get_user_by_email(email):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def get_user_by_id(user_id):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def create_user(email, pw_hash, salt, role="applicant"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (email, password_hash, salt, role) VALUES (%s,%s,%s,%s)",
        (email, pw_hash, salt, role)
    )
    uid = cur.lastrowid
    cur.close()
    conn.close()
    return uid


def update_last_login(email):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET last_login=%s WHERE email=%s",
        (datetime.utcnow(), email)
    )
    cur.close()
    conn.close()


#PASSWORD RESET
def store_reset_token(email, token, expiry):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET reset_token=%s, reset_expires_at=%s WHERE email=%s",
        (token, expiry, email)
    )
    cur.close()
    conn.close()


def clear_reset_token(email):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET reset_token=NULL, reset_expires_at=NULL WHERE email=%s",
        (email,)
    )
    cur.close()
    conn.close()


def set_new_password(email, pw_hash, salt):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET password_hash=%s, salt=%s WHERE email=%s",
        (pw_hash, salt, email)
    )
    cur.close()
    conn.close()


#SUBMISSIONS 
def create_submission(user_id, inputs, prediction, uploaded_files, confidence=None):
    """
    uploaded_files may contain Path / WindowsPath objects.
    Convert everything to string BEFORE json.dumps().

    Adds optional 'confidence' (numeric) — stored in the submissions.confidence column.
    """
    if isinstance(uploaded_files, dict):
        uploaded_files = {
            k: str(v) if isinstance(v, (Path, os.PathLike)) else v
            for k, v in uploaded_files.items()
        }

    conn = get_conn()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO submissions (user_id, inputs, prediction_result, uploaded_file_path, confidence)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            user_id,
            json.dumps(inputs),
            prediction,
            json.dumps(uploaded_files),
            float(confidence) if confidence is not None else None
        ))
    except Exception:
   
        cur.execute("""
            INSERT INTO submissions (user_id, inputs, prediction_result, uploaded_file_path)
            VALUES (%s,%s,%s,%s)
        """, (
            user_id,
            json.dumps(inputs),
            prediction,
            json.dumps(uploaded_files)
        ))
    finally:
        cur.close()
        conn.close()


def get_latest_submission_for_user(user_id):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT *
        FROM submissions
        WHERE user_id=%s
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def get_all_submissions():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT s.*, u.email AS applicant_email, r.email AS reviewed_by_email
        FROM submissions s
        JOIN users u ON s.user_id = u.id
        LEFT JOIN users r ON s.reviewed_by = r.id
        ORDER BY s.created_at DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def update_submission_status(submission_id, status, admin_id, note):
    """
    Update the submission's status, admin note, reviewer id and timestamp.
    This function is tolerant to either column naming:
      - admin_note (preferred if present)
      - admin_decision_note (fallback if admin_note does not exist)
    """
    conn = get_conn()
    cur = conn.cursor()
    # update admin_note
    try:
        cur.execute("""
            UPDATE submissions
            SET status=%s,
                admin_note=%s,
                reviewed_by=%s,
                reviewed_at=%s
            WHERE id=%s
        """, (
            status,
            note,
            admin_id,
            datetime.utcnow(),
            submission_id
        ))
        conn.commit()
    except mysql.connector.Error as e:
        #1054 = ER_BAD_FIELD_ERROR (unknown column) -> try alternate column name
        if getattr(e, "errno", None) == errorcode.ER_BAD_FIELD_ERROR or "Unknown column" in str(e):
            try:
                cur.execute("""
                    UPDATE submissions
                    SET status=%s,
                        admin_decision_note=%s,
                        reviewed_by=%s,
                        reviewed_at=%s
                    WHERE id=%s
                """, (
                    status,
                    note,
                    admin_id,
                    datetime.utcnow(),
                    submission_id
                ))
                conn.commit()
            except Exception as e2:
                cur.close()
                conn.close()
                raise
        else:
            cur.close()
            conn.close()
            raise
    finally:
        cur.close()
        conn.close()


def clear_all_submissions():
    """
    Delete all submissions (admin-only action). This clears backlog.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM submissions")
    try:
        cur.execute("ALTER TABLE submissions AUTO_INCREMENT = 1")
    except Exception:
        pass
    cur.close()
    conn.close()










