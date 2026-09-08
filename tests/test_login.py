def test_login_success(client):

    resp = client.post("/login", data={"email": "test@student.com", "password": "1234"}, follow_redirects=False)

    
    assert resp.status_code in (301, 302)
    assert "/dashboard" in resp.headers.get("Location", "")

def test_login_wrong_password(client):
    
    resp = client.post("/login", data={"email": "test@student.com", "password": "wrong"}, follow_redirects=True)

    assert resp.status_code == 200
    assert "البريد الإلكتروني أو كلمة المرور غير صحيحة" in resp.get_data(as_text=True)

def test_login_empty_fields(client):

    resp = client.post("/login", data={"email": "", "password": ""}, follow_redirects=True)

    assert resp.status_code == 200
    assert "تسجيل الدخول" in resp.get_data(as_text=True)
