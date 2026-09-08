import app as myapp

class DummyChoice:
    def __init__(self, content):
        self.message = type("msg", (), {"content": content})

class DummyResponse:
    def __init__(self, content):
        self.choices = [DummyChoice(content)]

def test_tc08_chatbot_returns_response(logged_in_client, monkeypatch):
   
    user_message = "Hi"
    mocked_reply = "Mocked chatbot reply"

   
    def fake_create(*args, **kwargs):
        return DummyResponse(mocked_reply)

    monkeypatch.setattr(myapp.client.chat.completions, "create", fake_create)

    resp = logged_in_client.post("/api/chatbot", json={
        "message": user_message,
        "history": []
    })

  
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["success"] is True
    
    assert data["response"] == mocked_reply



