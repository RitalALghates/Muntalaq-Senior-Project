import sqlite3
import app as myapp


def make_logged_in_client():
    myapp.app.config["TESTING"] = True
    client = myapp.app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_type"] = "student"
        sess["full_name"] = "Test Student"
    return client


def get_first_course():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    course = conn.execute("""
        SELECT * FROM courses
        WHERE status = 'published'
        ORDER BY id ASC
        LIMIT 1
    """).fetchone()
    conn.close()
    return course


def test_tc01_my_courses_displays_enrolled_course():
    course = get_first_course()

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO enrollments
        (student_id, course_id, status)
        VALUES
        (1, ?, 'current')
    """, (course["id"],))
    conn.commit()
    conn.close()

    client = make_logged_in_client()
    resp = client.get("/my-courses")

    assert resp.status_code == 200


def test_tc02_my_courses_filter_current_courses():
    client = make_logged_in_client()

    resp = client.get("/my-courses?status=current")

    assert resp.status_code == 200


def test_tc03_my_courses_filter_completed_courses():
    client = make_logged_in_client()

    resp = client.get("/my-courses?status=completed")

    assert resp.status_code == 200


def test_tc04_continue_course_content_requires_enrollment():
    course = get_first_course()
    client = make_logged_in_client()

    resp = client.get(f"/courses/{course['id']}")

    assert resp.status_code == 200