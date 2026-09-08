import sqlite3


def prepare_graduates_evaluation_tables(app):
    db_path = app.config["DATABASE"]
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        graduate_id INTEGER,
        title TEXT,
        status TEXT DEFAULT 'published',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS graduate_evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        graduate_id INTEGER,
        clarity INTEGER,
        content_value INTEGER,
        interaction INTEGER,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""INSERT INTO users 
        (full_name, email, phone, password, user_type, university, major, bio)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        ("Graduate Test", "graduate@test.com", "0550000000", "1234",
         "graduate", "University of Jeddah", "Software Engineering",
         "Graduate mentor"))

    c.execute("""INSERT INTO courses (graduate_id, title, status)
                 VALUES (?, ?, ?)""",
              (2, "React Basics", "published"))

    conn.commit()
    conn.close()


def test_display_graduates_evaluation_dashboard(logged_in_client):
    prepare_graduates_evaluation_tables(logged_in_client.application)

    response = logged_in_client.get("/graduates")

    assert response.status_code == 200
    assert b"Graduate Test" in response.data


def test_search_graduate_by_valid_name(logged_in_client):
    prepare_graduates_evaluation_tables(logged_in_client.application)

    response = logged_in_client.get("/graduates?q=Graduate")

    assert response.status_code == 200
    assert b"Graduate Test" in response.data


def test_search_graduate_by_invalid_name(logged_in_client):
    prepare_graduates_evaluation_tables(logged_in_client.application)

    response = logged_in_client.get("/graduates?q=NotExistingGraduate")

    assert response.status_code == 200


def test_submit_graduate_evaluation_with_valid_data(logged_in_client):
    prepare_graduates_evaluation_tables(logged_in_client.application)

    response = logged_in_client.post("/graduates/2/evaluate", data={
        "clarity": "5",
        "content_value": "4",
        "interaction": "5",
        "notes": "Excellent explanation"
    }, follow_redirects=True)

    assert response.status_code == 200


def test_submit_graduate_evaluation_with_missing_criteria(logged_in_client):
    prepare_graduates_evaluation_tables(logged_in_client.application)

    response = logged_in_client.post("/graduates/2/evaluate", data={
        "clarity": "",
        "content_value": "4",
        "interaction": "5",
        "notes": "Missing clarity value"
    }, follow_redirects=True)

    assert response.status_code in (200, 302)


def test_reset_graduate_evaluation_inputs(logged_in_client):
    prepare_graduates_evaluation_tables(logged_in_client.application)

    response = logged_in_client.get("/graduates")

    assert response.status_code == 200
    assert b"Excellent explanation" not in response.data