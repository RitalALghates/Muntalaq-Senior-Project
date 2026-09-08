def test_student_register_success(client):
    resp = client.post("/student-signup", data={
        "full_name": "New Student",
        "email": "new@student.com",
        "phone": "0500000000",
        "password": "Abcd12@",
        "confirm_password": "Abcd12@",
        "university": "جامعة الملك سعود",
        "major": "CS",
        "academic_year": "السنة الثانية"
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert "تم إنشاء الحساب بنجاح!" in resp.get_data(as_text=True)


def test_student_register_password_mismatch(client):
    resp = client.post("/student-signup", data={
        "full_name": "Mismatch Student",
        "email": "mismatch@student.com",
        "phone": "0500000000",
        "password": "123456",
        "confirm_password": "000000",
        "university": "Test Uni",
        "major": "CS",
        "academic_year": "السنة الثانية"
    }, follow_redirects=True)


    assert resp.status_code == 200
    assert "كلمات المرور غير متطابقة" in resp.get_data(as_text=True)

def test_student_register_duplicate_email(client):
    resp = client.post("/student-signup", data={
        "full_name": "Dup Student",
        "email": "test@student.com",
        "phone": "0500000000",
        "password": "Abcd12@",
        "confirm_password": "Abcd12@",
        "university": "جامعة الملك سعود",
        "major": "CS",
        "academic_year": "السنة الثانية"
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert "البريد الإلكتروني مستخدم بالفعل. يرجى استخدام بريد إلكتروني آخر" in resp.get_data(as_text=True)
