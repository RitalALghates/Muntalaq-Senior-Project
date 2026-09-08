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


def test_tc01_course_details_page_displays_course_information():
    course = get_first_course()
    client = make_logged_in_client()

    resp = client.get(f"/courses/{course['id']}")

    assert resp.status_code == 200
    assert course["title"] in resp.get_data(as_text=True)


def test_tc02_course_details_page_opens_successfully():
    course = get_first_course()
    client = make_logged_in_client()

    resp = client.get(f"/courses/{course['id']}")

    assert resp.status_code == 200
    assert "عن الدورة" in resp.get_data(as_text=True) or "محتوى الدورة" in resp.get_data(as_text=True)


def test_tc03_course_details_displays_instructor_information():
    course = get_first_course()
    client = make_logged_in_client()

    resp = client.get(f"/courses/{course['id']}")

    assert resp.status_code == 200
    assert "المدرب" in resp.get_data(as_text=True) or "instructor" in resp.get_data(as_text=True).lower()


def test_tc04_enroll_free_course_successfully():
    course = get_first_course()
    client = make_logged_in_client()

    resp = client.post(f"/courses/{course['id']}/enroll", follow_redirects=True)

    assert resp.status_code == 200