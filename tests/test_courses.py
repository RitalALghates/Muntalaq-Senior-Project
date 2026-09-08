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


def get_first_published_course():
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


def test_tc01_courses_page_displays_published_courses():
    course = get_first_published_course()
    client = make_logged_in_client()

    resp = client.get("/courses")

    assert resp.status_code == 200
    assert course["title"] in resp.get_data(as_text=True)


def test_tc02_courses_search_returns_matching_course():
    course = get_first_published_course()
    client = make_logged_in_client()

    resp = client.get(f"/courses?q={course['title']}")

    assert resp.status_code == 200
    assert course["title"] in resp.get_data(as_text=True)


def test_tc03_courses_free_filter_displays_successfully():
    client = make_logged_in_client()

    resp = client.get("/courses?price=free")

    assert resp.status_code == 200


def test_tc04_courses_paid_filter_displays_successfully():
    client = make_logged_in_client()

    resp = client.get("/courses?price=paid")

    assert resp.status_code == 200