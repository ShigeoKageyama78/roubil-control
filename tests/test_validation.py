from app.validation import nettoyer, valider_contact, valider_heure, valider_montant
from app.seed import purger_messages_anciens
from app.models import Message
from datetime import datetime, timedelta, timezone


def test_valider_contact_ok():
    donnees, erreurs = valider_contact("  Sara  ", "06 12 34 56 78", "Bonjour, une question.")
    assert not erreurs and donnees["nom"] == "Sara"


def test_valider_contact_erreurs():
    _, erreurs = valider_contact("A", "abc", "court")
    assert set(erreurs) == {"nom", "telephone", "contenu"}


def test_limites_de_longueur():
    _, erreurs = valider_contact("x" * 81, "0612345678", "y" * 1001)
    assert "nom" in erreurs and "contenu" in erreurs


def test_montant():
    assert valider_montant("380") == 380
    assert all(valider_montant(v) is None for v in ["0", "-1", "10001", "3.5", "abc", None, ""])


def test_heure():
    assert valider_heure("08:30") and valider_heure("23:59")
    assert not any(valider_heure(v) for v in ["24:00", "8:30", "12h30", "", None, "12:60"])


def test_nettoyer_supprime_caracteres_de_controle():
    assert nettoyer("a\x00b\x07c") == "abc"


def test_purge_des_anciens_messages(db):
    vieux = datetime.now(timezone.utc) - timedelta(days=100)
    db.add_all([Message(nom="vieux", telephone="0612345678", contenu="ancien message", cree_le=vieux),
                Message(nom="neuf", telephone="0612345678", contenu="récent message")])
    db.commit()
    assert purger_messages_anciens(db, 90) == 1
    assert [m.nom for m in db.query(Message)] == ["neuf"]
