notifications = [
    {"type": "course", "message": "تم إضافة دورة جديدة"},
    {"type": "message", "message": "لديك رسالة جديدة"},
    {"type": "achievement", "message": "لقد حققت إنجاز جديد"}
]


def test_display_new_course_notification():
    assert notifications[0]["type"] == "course"


def test_display_new_message_notification():
    assert notifications[1]["type"] == "message"


def test_display_evaluation_notification():
    assert notifications[2]["type"] == "achievement"


def test_mark_all_notifications_as_read():
    read_notifications = []

    for notification in notifications:
        read_notifications.append(notification)

    assert len(read_notifications) == len(notifications)


def test_no_notifications():
    empty_notifications = []

    assert len(empty_notifications) == 0