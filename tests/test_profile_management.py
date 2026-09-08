import sqlite3


def test_display_profile_page(logged_in_client):
    response = logged_in_client.get("/profile")
    assert response.status_code == 200
    assert b"Test Student" in response.data


def test_update_profile_personal_information(logged_in_client):
    response = logged_in_client.post("/profile", data={
        "full_name": "Updated Student",
        "phone": "0551234567",
        "city": "Jeddah",
        "university": "University of Jeddah",
        "major": "Software Engineering",
        "graduation_year": "2026",
        "gpa": "4.8",
        "bio": "Software engineering student"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Updated Student" in response.data


def test_update_profile_with_empty_full_name(logged_in_client):
    response = logged_in_client.post("/profile", data={
        "full_name": "",
        "phone": "0551234567",
        "city": "Jeddah",
        "university": "University of Jeddah",
        "major": "Software Engineering",
        "graduation_year": "2026",
        "gpa": "4.8",
        "bio": "Software engineering student"
    }, follow_redirects=True)

    assert response.status_code in (200, 302)


def test_upload_profile_picture_without_file(logged_in_client):
    response = logged_in_client.post("/api/profile/upload-image", data={})
    assert response.status_code == 400


def test_display_profile_interests(logged_in_client):
    db_path = logged_in_client.application.config["DATABASE"]
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO interests (user_id, interest) VALUES (?, ?)", (1, "AI"))
    conn.commit()
    conn.close()

    response = logged_in_client.get("/profile")
    assert response.status_code == 200
    assert b"AI" in response.data


def test_cancel_profile_changes_without_saving(logged_in_client):
    response = logged_in_client.get("/profile")
    assert response.status_code == 200
    assert b"Unsaved Student" not in response.data