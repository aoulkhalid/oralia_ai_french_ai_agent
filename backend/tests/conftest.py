"""
Fixtures partagées par tous les tests (Phase 8).

Principe : chaque test tourne contre une base SQLite en mémoire fraîche
(pas la vraie base PostgreSQL), via un override de la dépendance FastAPI
`get_db`. Le LLM n'est jamais appelé pour de vrai dans les tests : voir
la fixture `mock_llm` qui patche `generate_reply` / `correct_message`.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-tests-only")

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models import *  # noqa: F401,F403 - assure que tous les modèles sont enregistrés


@pytest.fixture()
def db_session():
    """Base SQLite en mémoire, recréée intégralement pour chaque test
    (isolation totale, aucun état ne fuite d'un test à l'autre)."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # SQLite désactive les contraintes de clé étrangère par défaut ; on les
    # active pour se rapprocher du comportement réel de PostgreSQL.
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    """TestClient FastAPI avec la dépendance get_db redirigée vers la
    session de test SQLite en mémoire."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def mock_llm(monkeypatch):
    """Remplace les appels LLM réels par des réponses déterministes."""
    from app.services import llm_service

    def fake_generate_reply(message, niveau_cecrl="A1", historique=None, scenario_context=None):
        return "Bonjour ! Comment allez-vous aujourd'hui ?"

    def fake_correct_message(message):
        return {"has_errors": False, "erreurs": []}

    monkeypatch.setattr(llm_service, "generate_reply", fake_generate_reply)
    monkeypatch.setattr(llm_service, "correct_message", fake_correct_message)
    return llm_service


@pytest.fixture()
def registered_user_headers(client):
    """Crée un utilisateur de test et renvoie les headers d'authentification prêts à l'emploi."""
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    resp = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "password123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
