import os
import sqlite3
import hashlib
import secrets
import hmac

# ==========================================
# DATABASE PATH
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_NAME = os.path.join(BASE_DIR, "studentcareerai.db")


# ==========================================
# CREATE USERS TABLE
# ==========================================

def create_auth_table():
    connection = sqlite3.connect(DATABASE_NAME)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL
            )
        """)

        connection.commit()

    finally:
        connection.close()


# ==========================================
# PASSWORD HASHING
# ==========================================

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        200000
    ).hex()

    return password_hash, salt


# ==========================================
# REGISTER NEW USER
# ==========================================

def register_user(username, password):
    username = username.strip()

    if not username or not password:
        return False, "Enter a username and password."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    password_hash, salt = hash_password(password)

    connection = sqlite3.connect(DATABASE_NAME)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO users (username, password_hash, salt)
            VALUES (?, ?, ?)
        """, (username, password_hash, salt))

        connection.commit()

        return True, "Registration successful!"

    except sqlite3.IntegrityError:
        return False, "This username already exists."

    except sqlite3.Error:
        return False, "A database error occurred. Please try again."

    finally:
        connection.close()


# ==========================================
# LOGIN EXISTING USER
# ==========================================

def login_user(username, password):
    username = username.strip()

    if not username or not password:
        return False

    connection = sqlite3.connect(DATABASE_NAME)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT password_hash, salt
            FROM users
            WHERE username = ?
        """, (username,))

        user = cursor.fetchone()

        if user is None:
            return False

        saved_hash, salt = user

        entered_hash, _ = hash_password(password, salt)

        return hmac.compare_digest(
            saved_hash,
            entered_hash
        )

    except sqlite3.Error:
        return False

    finally:
        connection.close()


# ==========================================
# INITIALIZE AUTHENTICATION
# ==========================================

create_auth_table()