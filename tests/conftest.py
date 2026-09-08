import sqlite3
import pytest
import app as myapp
from werkzeug.security import generate_password_hash


@pytest.fixture
def client():
    myapp.app.config["TESTING"] = True

    with myapp.app.test_client() as client:
        yield client


@pytest.fixture
def logged_in_client(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_type"] = "student"
        sess["full_name"] = "Test Student"
        sess["user_email"] = "test@student.com"

    return client


@pytest.fixture
def db_path():
    return "database.db"


@pytest.fixture(autouse=True)
def setup_course_tables():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        password TEXT NOT NULL,
        user_type TEXT NOT NULL,
        university TEXT,
        major TEXT,
        graduation_year INTEGER,
        academic_year TEXT,
        gpa REAL,
        city TEXT,
        bio TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        graduate_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        price REAL DEFAULT 0,
        duration TEXT,
        level TEXT,
        field TEXT,
        tags TEXT,
        image TEXT DEFAULT 'course1.jpg',
        status TEXT DEFAULT 'published',
        rating REAL DEFAULT 0,
        reviews_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        progress INTEGER DEFAULT 0,
        status TEXT DEFAULT 'current',
        enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(student_id, course_id)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        video_url TEXT,
        duration TEXT,
        order_idx INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, course_id)
    )
    """)

    c.execute("""
    INSERT OR IGNORE INTO users
    (id, full_name, email, phone, password, user_type, university, major)
    VALUES
    (1, 'Test Student', 'student@test.com', '0500000000', ?, 'student', 'UJ', 'SE')
    """, (generate_password_hash("Test@123"),))

    c.execute("""
    INSERT OR IGNORE INTO users
    (id, full_name, email, phone, password, user_type, university, major)
    VALUES
    (2, 'Ahmed Salem', 'graduate@test.com', '0555555555', ?, 'graduate', 'UJ', 'SE')
    """, (generate_password_hash("Test@123"),))

    c.execute("""
    INSERT OR IGNORE INTO courses
    (id, graduate_id, title, description, price, duration, level, field, tags, image, status)
    VALUES
    (1, 2, 'Web Development Course', 'Learn HTML CSS JavaScript', 0, '6 weeks', 'Beginner', 'Web Development', 'HTML,CSS', 'course1.jpg', 'published')
    """)

    c.execute("""
    INSERT OR IGNORE INTO courses
    (id, graduate_id, title, description, price, duration, level, field, tags, image, status)
    VALUES
    (2, 2, 'Python Paid Course', 'Learn Python programming', 199, '8 weeks', 'Intermediate', 'Programming', 'Python', 'course2.jpg', 'published')
    """)

    c.execute("""
    INSERT OR IGNORE INTO lessons
    (id, course_id, title, video_url, duration, order_idx)
    VALUES
    (1, 1, 'Introduction Lesson', 'https://youtube.com/test', '10:00', 1)
    """)

    conn.commit()
    conn.close()