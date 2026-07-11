def test_dashboard_for_brand_new_user_is_empty_but_valid(client, registered_user_headers):
    resp = client.get("/progress/1/dashboard", headers=registered_user_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["conversations_completees"] == 0
    assert data["erreurs_frequentes"] == []
    # Le niveau de départ (A1) est déjà tracé dans l'historique dès
    # l'inscription (voir auth.py::register) : la courbe de progression a
    # ainsi toujours un point de départ visible, même avant la première
    # conversation.
    assert len(data["niveau_historique"]) == 1
    assert data["niveau_historique"][0]["niveau"] == "A1"


def test_dashboard_forbidden_for_other_users(client, registered_user_headers):
    resp = client.get("/progress/9999/dashboard", headers=registered_user_headers)
    assert resp.status_code == 403


def test_niveau_historique_has_starting_point_after_registration(client):
    client.post(
        "/auth/register",
        json={"email": "niveau@example.com", "password": "password123"},
    )
    resp = client.post(
        "/auth/login",
        data={"username": "niveau@example.com", "password": "password123"},
    )
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

    resp = client.get("/progress/1/dashboard", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["niveau_historique"]) == 1





def test_level_up_after_five_error_free_conversations(client, registered_user_headers, mock_llm):
    for _ in range(5):
        resp = client.post(
            "/chat", json={"message": "Bonjour"}, headers=registered_user_headers
        )
        conv_id = resp.json()["conversation_id"]
        client.post(f"/chat/{conv_id}/close", headers=registered_user_headers)

    resp = client.get("/progress/1/dashboard", headers=registered_user_headers)
    data = resp.json()
    assert data["niveau_estime"] == "A2"  # monté de A1 à A2
    assert len(data["niveau_historique"]) == 2  # point de départ + montée


def test_points_awarded_for_error_free_messages(client, registered_user_headers, mock_llm):
    client.post("/chat", json={"message": "Bonjour"}, headers=registered_user_headers)
    resp = client.get("/progress/1/dashboard", headers=registered_user_headers)
    assert resp.json()["points"] > 0


def test_badge_awarded_after_first_conversation(client, registered_user_headers, mock_llm):
    resp = client.post(
        "/chat", json={"message": "Bonjour"}, headers=registered_user_headers
    )
    conv_id = resp.json()["conversation_id"]
    client.post(f"/chat/{conv_id}/close", headers=registered_user_headers)

    resp = client.get("/progress/1/dashboard", headers=registered_user_headers)
    badge_ids = [b["id"] for b in resp.json()["badges"]]
    assert "first_conversation" in badge_ids
