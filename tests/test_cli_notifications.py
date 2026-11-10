import smtplib
from dataclasses import replace

from sqlalchemy import select

from app import cli
from app.database import creer_engine, creer_session_factory
from app.models import Administrateur
from app.notifications import notifier_nouveau_message
from app.security import verifier_mot_de_passe


def test_create_admin(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/t.sqlite3")
    monkeypatch.setattr(cli.getpass, "getpass", lambda *_: "mot-de-passe-12345")
    assert cli.main(["create-admin", "gerant"]) == 0
    with creer_session_factory(creer_engine(f"sqlite:///{tmp_path}/t.sqlite3"))() as db:
        compte = db.scalar(select(Administrateur))
        assert compte.identifiant == "gerant"
        assert verifier_mot_de_passe(compte.mot_de_passe_hash, "mot-de-passe-12345")


def test_create_admin_mot_de_passe_trop_court(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/t.sqlite3")
    monkeypatch.setattr(cli.getpass, "getpass", lambda *_: "court")
    assert cli.main(["create-admin", "gerant"]) == 1


def test_purge_cli(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/t.sqlite3")
    assert cli.main(["purge"]) == 0
    assert "0 message" in capsys.readouterr().out


def test_notification_inactive_sans_smtp(settings, monkeypatch):
    def interdit(*a, **k):
        raise AssertionError("aucune connexion SMTP attendue")
    monkeypatch.setattr(smtplib, "SMTP", interdit)
    notifier_nouveau_message(settings, "A", "0612345678", "bonjour")


def test_notification_corps_sans_injection_d_en_tete(settings, monkeypatch):
    envoyes = []

    class FauxSMTP:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self, **k): pass
        def login(self, *a): pass
        def send_message(self, mail): envoyes.append(mail)

    monkeypatch.setattr(smtplib, "SMTP", FauxSMTP)
    reglages = replace(settings, smtp_host="smtp.test", notify_to="gerant@example.org")
    notifier_nouveau_message(reglages, "Nom\r\nBcc: pirate@example.org", "0612345678", "message")
    assert len(envoyes) == 1 and envoyes[0]["Bcc"] is None
    assert envoyes[0]["Subject"] == "Nouveau message depuis le site ROUBIL CONTROLE"


def test_notification_erreur_smtp_ne_plante_pas(settings, monkeypatch):
    def echec(*a, **k):
        raise OSError("réseau coupé")
    monkeypatch.setattr(smtplib, "SMTP", echec)
    notifier_nouveau_message(replace(settings, smtp_host="x", notify_to="y@z.org"), "A", "0612345678", "m")
