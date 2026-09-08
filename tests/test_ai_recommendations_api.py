import app as myapp

class DummyChoice:
    def __init__(self, content):
        self.message = type("msg", (), {"content": content})

class DummyResponse:
    def __init__(self, content):
        self.choices = [DummyChoice(content)]

def test_ai_recommendations_returns_courses_with_mock(logged_in_client, monkeypatch):
    fake_json = """
    {
      "recommended_course_ids": [1, 2],
      "advice": ["x"],
      "learning_path": "y",
      "personalized_message": "z"
    }
    """

    def fake_create(*args, **kwargs):
        return DummyResponse(fake_json)

 
    monkeypatch.setattr(myapp.client.chat.completions, "create", fake_create)

    resp = logged_in_client.post("/api/ai-recommendations", json={
        "major": "CS",
        "interests": "AI",
        "career_goals": "Data Scientist",
        "skill_level": "Beginner"
    })

    assert resp.status_code == 200
    data = resp.get_json()
    assert "courses" in data
    assert len(data["courses"]) > 0
