def test_chat_creates_conversation_and_saves_messages(client, registered_user_headers, mock_llm):
    resp = client.post(
        "/chat",
        json={"message": "Bonjour, comment vas-tu ?"},
        headers=registered_user_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["conversation_id"] is not None
    assert data["reply"]
    assert data["corrections"] == []


def test_chat_requires_authentication(client, mock_llm):
    resp = client.post("/chat", json={"message": "Bonjour"})
    assert resp.status_code == 401


def test_chat_conversation_history(client, registered_user_headers, mock_llm):
    resp = client.post(
        "/chat", json={"message": "Salut"}, headers=registered_user_headers
    )
    conv_id = resp.json()["conversation_id"]

    resp = client.get(f"/chat/{conv_id}/history", headers=registered_user_headers)
    assert resp.status_code == 200
    messages = resp.json()
    assert len(messages) == 2  # message utilisateur + réponse assistant
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_chat_close_conversation_increments_counter(client, registered_user_headers, mock_llm):
    resp = client.post(
        "/chat", json={"message": "Salut"}, headers=registered_user_headers
    )
    conv_id = resp.json()["conversation_id"]

    resp = client.post(f"/chat/{conv_id}/close", headers=registered_user_headers)
    assert resp.status_code == 200
    assert resp.json()["ended_at"] is not None

    resp = client.get("/progress/1/dashboard", headers=registered_user_headers)
    assert resp.json()["conversations_completees"] == 1


def test_chat_with_unknown_conversation_id_creates_new_one(
    client, registered_user_headers, mock_llm
):
    resp = client.post(
        "/chat",
        json={"message": "Salut", "conversation_id": 9999},
        headers=registered_user_headers,
    )
    assert resp.status_code == 200
    # 9999 n'existe pas / n'appartient pas à l'utilisateur -> une nouvelle
    # conversation est créée plutôt que de planter.
    assert resp.json()["conversation_id"] != 9999


def test_chat_with_scenario_injects_context(client, registered_user_headers, db_session):
    from app.models.scenario import Scenario
    from app.services import llm_service

    scenario = Scenario(
        titre="Au restaurant",
        contexte_prompt="Tu joues le rôle d'un serveur.",
        niveau_cecrl="A1",
        categorie="quotidien",
    )
    db_session.add(scenario)
    db_session.commit()
    db_session.refresh(scenario)

    captured = {}

    def fake_generate_reply(message, niveau_cecrl="A1", historique=None, scenario_context=None):
        captured["scenario_context"] = scenario_context
        return "Bienvenue au restaurant !"

    def fake_correct_message(message):
        return {"has_errors": False, "erreurs": []}

    llm_service.generate_reply = fake_generate_reply
    llm_service.correct_message = fake_correct_message

    resp = client.post(
        "/chat",
        json={"message": "Bonjour", "scenario_id": scenario.id},
        headers=registered_user_headers,
    )
    assert resp.status_code == 200
    assert captured["scenario_context"] == "Tu joues le rôle d'un serveur."
