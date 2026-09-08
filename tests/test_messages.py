import sqlite3
import pytest
from werkzeug.security import generate_password_hash
import app as myapp


@pytest.fixture()
def messages_client(tmp_path):
    test_db = tmp_path / "test_messages.db"

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
            profile_image TEXT,
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
        CREATE TABLE course_offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            progress INTEGER DEFAULT 0,
            UNIQUE(student_id, course_id)
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
        "Test Student",
        "student@test.com",
        generate_password_hash("1234"),
        "student"
    ))

    c.execute("""
        INSERT INTO users (full_name, email, password, user_type, major, university)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "Rital Yahya",
        "graduate@test.com",
        generate_password_hash("1234"),
        "graduate",
        "software",
        "King Abdulaziz University"
    ))

    c.execute("""
        INSERT INTO courses (
            graduate_id, title, description, price, duration,
            level, field, tags, image, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        2,
        "React.js Basics in 90 Mins",
        "React basics course",
        0,
        "5 weeks",
        "Beginner",
        "Web Development",
        "React",
        "course1.jpg",
        "published"
    ))

    c.execute("""
        INSERT INTO chat_messages (sender_id, receiver_id, content)
        VALUES (?, ?, ?)
    """, (
        1,
        2,
        "Hello"
    ))

    conn.commit()
    conn.close()

    with myapp.app.test_client() as client:
        yield client


def login_as_student(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Test Student"
        sess["user_type"] = "student"
        sess["user_email"] = "student@test.com"


def login_as_graduate(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 2
        sess["user_name"] = "Rital Yahya"
        sess["user_type"] = "graduate"
        sess["user_email"] = "graduate@test.com"


def test_view_messages_list(messages_client):
    login_as_student(messages_client)

    response = messages_client.get("/messages", follow_redirects=True)
    page_text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Rital Yahya" in page_text


def test_start_chat_with_graduate(messages_client):
    login_as_student(messages_client)

    response = messages_client.post(
        "/api/messages/start",
        json={"partner_id": 2}
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert "/messages?with=2" in data["url"]


def test_send_text_message(messages_client):
    login_as_student(messages_client)

    response = messages_client.post(
        "/api/messages/send",
        json={
            "receiver_id": 2,
            "content": "Hello graduate"
        }
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True


def test_prevent_academic_violation_message(messages_client):
    login_as_student(messages_client)

    response = messages_client.post(
        "/api/messages/send",
        json={
            "receiver_id": 2,
            "content": "حل الواجب"
        }
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is False
    assert data["moderated"] is True


def test_share_course_offer_card(messages_client):
    login_as_graduate(messages_client)

    response = messages_client.post(
        "/api/messages/share-course",
        json={
            "receiver_id": 1,
            "course_id": 1
        }
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True


def test_student_accepts_course_offer(messages_client):
    login_as_graduate(messages_client)

    messages_client.post(
        "/api/messages/share-course",
        json={
            "receiver_id": 1,
            "course_id": 1
        }
    )

    login_as_student(messages_client)

    response = messages_client.post(
        "/api/offer/1/respond",
        json={"action": "accept"}
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert data["status"] == "accepted"


def test_student_rejects_course_offer(messages_client):
    login_as_graduate(messages_client)

    messages_client.post(
        "/api/messages/share-course",
        json={
            "receiver_id": 1,
            "course_id": 1
        }
    )

    login_as_student(messages_client)

    response = messages_client.post(
        "/api/offer/1/respond",
        json={"action": "reject"}
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert data["status"] == "rejected"