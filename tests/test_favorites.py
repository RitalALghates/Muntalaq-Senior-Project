course = {
    "id": 1,
    "title": "أساسيات تصميم واجهة المستخدم"
}


def test_add_course_to_favorites():
    favorites = []

    favorites.append(course)

    assert course in favorites


def test_remove_course_from_favorites():
    favorites = [course]

    favorites.remove(course)

    assert course not in favorites


def test_prevent_duplicate_favorites():
    favorites = []

    if course not in favorites:
        favorites.append(course)

    if course not in favorites:
        favorites.append(course)

    assert favorites.count(course) == 1


def test_display_saved_favorites():
    favorites = [course]

    assert len(favorites) == 1
    assert favorites[0]["title"] == "أساسيات تصميم واجهة المستخدم"