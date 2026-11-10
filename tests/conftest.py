"""Fixtures communes : une application neuve avec une base SQLite EN MÉMOIRE pour chaque test,
donc des tests isolés, rapides et qui ne touchent jamais aux vraies données."""
import re

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.database import Base, creer_engine, creer_session_factory
from app.main import create_app
from app.models import Administrateur
from app.security import hacher_mot_de_passe

MOT_DE_PASSE = "un-mot-de-passe-solide-123"


@pytest.fixture
def settings():
    return Settings(secret_key="cle-de-test", database_url="sqlite:///:memory:", cookie_secure=False,
                    smtp_host="", smtp_port=587, smtp_user="", smtp_password="", notify_to="", retention_days=90)


@pytest.fixture
def engine(settings):
    return creer_engine(settings.database_url)


@pytest.fixture
def client(settings, engine):
    app = create_app(settings, engine)
    with TestClient(app) as c:   # le « with » déclenche le démarrage (tables + données initiales)
        c.app_ref = app
        yield c


@pytest.fixture
def db(client):
    with client.app_ref.state.session_factory() as session:
        yield session


@pytest.fixture
def admin(db):
    db.add(Administrateur(identifiant="gerant", mot_de_passe_hash=hacher_mot_de_passe(MOT_DE_PASSE)))
    db.commit()


def extraire_csrf(html: str) -> str:
    return re.search(r'name="csrf" value="([^"]+)"', html).group(1)


def jeton(client, chemin="/"):
    return extraire_csrf(client.get(chemin).text)


@pytest.fixture
def connecte(client, admin):
    r = client.post("/admin/login", data={"identifiant": "gerant", "mot_de_passe": MOT_DE_PASSE,
                                          "csrf": jeton(client, "/admin/login")}, follow_redirects=False)
    assert r.status_code == 303
    return client
