import sqlite3

DATABASE_NAME = "studentcareerai.db"


def create_database():
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            name TEXT NOT NULL DEFAULT '',
            branch TEXT DEFAULT '',
            course TEXT DEFAULT '',
            year TEXT DEFAULT '',
            skills TEXT DEFAULT '',
            interests TEXT DEFAULT '',
            career_goal TEXT DEFAULT ''
        )
    """)

    # Add missing columns to an existing database.
    # Existing student records will be preserved.
    cursor.execute("PRAGMA table_info(students)")
    existing_columns = {
        column[1] for column in cursor.fetchall()
    }

    required_columns = {
        "username": "TEXT",
        "name": "TEXT NOT NULL DEFAULT ''",
        "branch": "TEXT DEFAULT ''",
        "course": "TEXT DEFAULT ''",
        "year": "TEXT DEFAULT ''",
        "skills": "TEXT DEFAULT ''",
        "interests": "TEXT DEFAULT ''",
        "career_goal": "TEXT DEFAULT ''"
    }

    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            cursor.execute(
                f"ALTER TABLE students ADD COLUMN "
                f"{column_name} {column_type}"
            )

    connection.commit()
    connection.close()


def save_student(name, course, year, skills, interests):
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO students
        (name, course, year, skills, interests)
        VALUES (?, ?, ?, ?, ?)
    """, (
        name,
        course,
        year,
        ", ".join(skills),
        ", ".join(interests)
    ))

    connection.commit()
    connection.close()


def get_all_students():
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, course, year, skills, interests
        FROM students
        ORDER BY id DESC
    """)

    students = cursor.fetchall()
    connection.close()

    return students