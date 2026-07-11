def test_list_scenarios_empty_by_default(client, registered_user_headers):
    resp = client.get("/scenarios", headers=registered_user_headers)
    assert resp.status_code == 200
    assert resp.json() == []  # aucune donnée de seed dans les tests (SQLite en mémoire)


def test_scenario_filtering(client, registered_user_headers, db_session):
    from app.models.scenario import Scenario

    db_session.add_all(
        [
            Scenario(titre="Restaurant", niveau_cecrl="A1", categorie="quotidien"),
            Scenario(titre="DELF B1 oral", niveau_cecrl="B1", categorie="delf"),
        ]
    )
    db_session.commit()

    resp = client.get("/scenarios?categorie=delf", headers=registered_user_headers)
    assert resp.status_code == 200
    titres = [s["titre"] for s in resp.json()]
    assert titres == ["DELF B1 oral"]


def test_generate_exercise_and_submit_correct_answer(
    client, registered_user_headers, monkeypatch
):
    from app.services import exercise_service
    import json

    class FakeChoice:
        class message:
            content = json.dumps(
                {"question": "Complétez : je ___ content.", "reponse_attendue": "suis"}
            )

    class FakeResponse:
        choices = [FakeChoice()]

    monkeypatch.setattr(
        exercise_service, "_create_completion", lambda **kwargs: FakeResponse()
    )

    resp = client.post("/exercises/generate", headers=registered_user_headers)
    assert resp.status_code == 200
    exercise_id = resp.json()["id"]
    assert "reponse_attendue" not in resp.json()  # jamais révélée avant correction

    resp = client.post(
        f"/exercises/{exercise_id}/submit",
        json={"reponse": "suis"},
        headers=registered_user_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["is_correct"] is True


def test_submit_exercise_wrong_answer(client, registered_user_headers, monkeypatch):
    from app.services import exercise_service
    import json

    class FakeChoice:
        class message:
            content = json.dumps(
                {"question": "Complétez : je ___ content.", "reponse_attendue": "suis"}
            )

    class FakeResponse:
        choices = [FakeChoice()]

    monkeypatch.setattr(
        exercise_service, "_create_completion", lambda **kwargs: FakeResponse()
    )

    resp = client.post("/exercises/generate", headers=registered_user_headers)
    exercise_id = resp.json()["id"]

    resp = client.post(
        f"/exercises/{exercise_id}/submit",
        json={"reponse": "mauvaise réponse"},
        headers=registered_user_headers,
    )
    assert resp.json()["is_correct"] is False


def test_teacher_endpoints_forbidden_for_students(client, registered_user_headers):
    resp = client.get("/teacher/students", headers=registered_user_headers)
    assert resp.status_code == 403


def test_teacher_can_list_students(client, registered_user_headers, db_session):
    from app.models.user import User

    user = db_session.query(User).filter(User.email == "test@example.com").first()
    user.role = "teacher"
    db_session.commit()

    resp = client.get("/teacher/students", headers=registered_user_headers)
    assert resp.status_code == 200
    assert resp.json() == []  # le compte enseignant lui-même n'est pas un "student"
