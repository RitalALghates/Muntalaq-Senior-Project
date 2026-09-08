settings = {
    "language": "English",
    "notifications": True,
    "logged_in": True
}


def test_change_language_to_arabic():
    settings["language"] = "Arabic"

    assert settings["language"] == "Arabic"


def test_change_language_to_english():
    settings["language"] = "English"

    assert settings["language"] == "English"


def test_disable_notifications_setting():
    settings["notifications"] = False

    assert settings["notifications"] is False


def test_enable_notifications_setting():
    settings["notifications"] = True

    assert settings["notifications"] is True


def test_logout():
    settings["logged_in"] = False

    assert settings["logged_in"] is False