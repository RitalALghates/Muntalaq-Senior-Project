import sqlite3
import pytest
from werkzeug.security import generate_password_hash
import app as myapp


@pytest.fixture()
def community_client(tmp_path):
    test_db = tmp_path / "test_community.db"

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
            academic_year TEXT,
            profile_image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE post_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, post_id)
        )
    """)

    c.execute("""
        CREATE TABLE post_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            icon TEXT DEFAULT '👥',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            group_id INTEGER NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, group_id)
        )
    """)

    c.execute("""
        CREATE TABLE group_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
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
        "Test Student",
        "student@test.com",
        generate_password_hash("1234"),
        "student"
    ))

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
        INSERT INTO groups (name, description, icon)
        VALUES (?, ?, ?)
    """, (
        "Web Developers",
        "Community for web developers and UI designers",
        "💻"
    ))

    c.execute("""
        INSERT INTO posts (user_id, content, tags)
        VALUES (?, ?, ?)
    """, (
        1,
        "Artificial Intelligence is a broad concept that includes Machine Learning.",
        "AI, Machine Learning"
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


def test_display_community_page(community_client):
    login_as_student(community_client)

    response = community_client.get("/community", follow_redirects=True)
    page_text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Web Developers" in page_text


def test_join_community_group(community_client):
    login_as_student(community_client)

    response = community_client.post(
        "/community/groups/1/join",
        follow_redirects=False
    )

    assert response.status_code in (301, 302)


def test_send_message_in_group_chat(community_client):
    login_as_student(community_client)

    community_client.post("/community/groups/1/join")

    response = community_client.post(
        "/api/groups/1/messages",
        json={"content": "HELLO"}
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert any(message["content"] == "HELLO" for message in data["messages"])


def test_create_new_community_post(community_client):
    login_as_student(community_client)

    response = community_client.post(
        "/community/posts/new",
        data={
            "content": "Deep Learning is a branch of Artificial Intelligence.",
            "tags": "Deep Learning"
        },
        follow_redirects=True
    )

    page_text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Deep Learning" in page_text


def test_search_posts_by_keyword(community_client):
    login_as_student(community_client)

    response = community_client.get(
        "/community/posts?q=Machine Learning",
        follow_redirects=True
    )

    page_text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Machine Learning" in page_text


def test_like_post(community_client):
    login_as_student(community_client)

    response = community_client.post("/api/posts/1/like")
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert data["liked"] is True
    assert data["count"] == 1


def test_comment_on_post(community_client):
    login_as_student(community_client)

    response = community_client.post(
        "/api/posts/1/comment",
        json={"content": "Machine Learning is useful."}
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert data["count"] == 1


def test_view_trending_topics(community_client):
    login_as_student(community_client)

    response = community_client.get("/community", follow_redirects=True)
    page_text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Machine Learning" in page_text