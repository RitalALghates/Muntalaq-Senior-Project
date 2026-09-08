import sqlite3


def prepare_dashboard_tables(app):
    db_path = app.config["DATABASE"]
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        graduate_id INTEGER,
        title TEXT,
        image TEXT,
        status TEXT DEFAULT 'published',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        course_id INTEGER,
        status TEXT DEFAULT 'active',
        progress INTEGER DEFAULT 0,
        enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        title TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS lesson_completions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        lesson_id INTEGER,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        message TEXT,
        notif_type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""INSERT INTO users (full_name, email, password, user_type, major)
                 VALUES (?, ?, ?, ?, ?)""",
              ("Graduate Test", "graduate@test.com", "1234", "graduate", "Software Engineering"))

    c.execute("""INSERT INTO courses (graduate_id, title, image, status)
                 VALUES (?, ?, ?, ?)""",
              (2, "Python Basics", "course.jpg", "published"))

    c.execute("""INSERT INTO enrollments (student_id, course_id, status, progress)
                 VALUES (?, ?, ?, ?)""",
              (1, 1, "active", 50))

    c.execute("""INSERT INTO lessons (course_id, title)
                 VALUES (?, ?)""",
              (1, "Lesson 1"))

    c.execute("""INSERT INTO lesson_completions (student_id, lesson_id)
                 VALUES (?, ?)""",
              (1, 1))

    c.execute("""INSERT INTO notifications (user_id, title, message, notif_type)
                 VALUES (?, ?, ?, ?)""",
              (1, "New Activity", "You completed a lesson", "achievement"))

    conn.commit()
    conn.close()


def test_display_student_dashboard(logged_in_client):
    prepare_dashboard_tables(logged_in_client.application)

    response = logged_in_client.get("/dashboard")

    assert response.status_code == 200
    assert b"Dashboard" in response.data or b"dashboard" in response.data


def test_dashboard_requires_login(client):
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302


def test_student_dashboard_displays_continue_learning(logged_in_client):
    prepare_dashboard_tables(logged_in_client.application)

    response = logged_in_client.get("/dashboard")

    assert response.status_code == 200
    assert b"Python Basics" in response.data


def test_student_dashboard_displays_latest_activity(logged_in_client):
    prepare_dashboard_tables(logged_in_client.application)

    response = logged_in_client.get("/dashboard")

    assert response.status_code == 200
    assert b"New Activity" in response.data


def test_student_dashboard_with_no_enrolled_courses(logged_in_client):
    prepare_dashboard_tables(logged_in_client.application)

    db_path = logged_in_client.application.config["DATABASE"]
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM lesson_completions")
    conn.execute("DELETE FROM lessons")
    conn.execute("DELETE FROM enrollments")
    conn.execute("DELETE FROM courses")
    conn.commit()
    conn.close()

    response = logged_in_client.get("/dashboard")

    assert response.status_code == 200
    assert b"Python Basics" not in response.data


def test_student_dashboard_displays_progress_summary(logged_in_client):
    prepare_dashboard_tables(logged_in_client.application)

    response = logged_in_client.get("/dashboard")

    assert response.status_code == 200
    assert b"50" in response.data or b"Progress" in response.data or b"progress" in response.data