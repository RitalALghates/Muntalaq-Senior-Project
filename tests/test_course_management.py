import sqlite3
import pytest
from werkzeug.security import generate_password_hash
import app as myapp


@pytest.fixture()
def course_client(tmp_path):
    test_db = tmp_path / "test_course.db"

    myapp.app.config["TESTING"] = True
    myapp.app.config["DATABASE"] = str(test_db)

    conn = sqlite3.connect(str(test_db))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        CREATE TABLE users (
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
            bio TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            graduate_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL DEFAULT 0,
            duration TEXT,
            level TEXT,
            field TEXT,
            tags TEXT,
            image TEXT,
            status TEXT DEFAULT 'published',
            rating REAL DEFAULT 0,
            reviews INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            message_type TEXT DEFAULT 'text',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            notif_type TEXT DEFAULT 'general',
            link TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        INSERT INTO users (full_name, email, password, user_type)
        VALUES (?, ?, ?, ?)
    """, (
        "Test Graduate",
        "graduate@test.com",
        generate_password_hash("1234"),
        "graduate"
    ))

    c.execute("""
        INSERT INTO courses (
            graduate_id, title, description, price, duration,
            level, field, tags, image, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        1,
        "Web Development using React",
        "Software dev",
        199,
        "6 weeks",
        "Advanced",
        "Web Development",
        "react",
        "course1.jpg",
        "published"
    ))

    conn.commit()
    conn.close()

    with myapp.app.test_client() as client:
        yield client


def login_as_graduate(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Test Graduate"
        sess["user_type"] = "graduate"
        sess["user_email"] = "graduate@test.com"


def test_create_course_successfully(course_client):
    login_as_graduate(course_client)

    response = course_client.post("/courses/new", data={
        "title": "Web Development using React",
        "description": "Software dev",
        "price": "199",
        "duration": "6 weeks",
        "level": "Advanced",
        "field": "Web Development",
        "tags": "react",
        "image": "course1.jpg"
    }, follow_redirects=False)

    assert response.status_code in (301, 302)
    assert "/lessons" in response.headers.get("Location", "")


def test_create_course_missing_title(course_client):
    login_as_graduate(course_client)

    response = course_client.post("/courses/new", data={
        "title": "",
        "description": "ai",
        "price": "99",
        "duration": "5 weeks",
        "level": "Medium",
        "field": "ai",
        "tags": "backend",
        "image": "course5.jpg"
    }, follow_redirects=True)

    page_text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "backend" not in page_text


def test_cancel_course_successfully(course_client):
    login_as_graduate(course_client)

    response = course_client.post(
        "/courses/1/cancel",
        follow_redirects=False
    )

    assert response.status_code in (301, 302)


def test_republish_course_successfully(course_client):
    login_as_graduate(course_client)

    course_client.post(
        "/courses/1/cancel",
        follow_redirects=False
    )

    response = course_client.post(
        "/courses/1/republish",
        follow_redirects=False
    )

    assert response.status_code in (301, 302)