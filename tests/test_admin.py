from app.models import Administrateur, Horaire, Message, Prestation
from app.security import hacher_mot_de_passe, mot_de_passe_assez_fort, verifier_mot_de_passe
from tests.conftest import MOT_DE_PASSE, jeton


def test_admin_redirige_vers_login_sans_connexion(client):
    r = client.get("/admin/", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/admin/login"


def test_post_admin_sans_connexion_refuse(client):
    r = client.post("/admin/tarifs/1", data={"montant_dh": "1", "csrf": "x"}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/admin/login"


def test_login_mauvais_mot_de_passe(client, admin):
    r = client.post("/admin/login", data={"identifiant": "gerant", "mot_de_passe": "faux",
                                          "csrf": jeton(client, "/admin/login")})
    assert r.status_code == 401 and "incorrect" in r.text


def test_login_identifiant_inconnu_meme_message(client, admin):
    r = client.post("/admin/login", data={"identifiant": "inconnu", "mot_de_passe": "x",
                                          "csrf": jeton(client, "/admin/login")})
    assert r.status_code == 401 and "Identifiant ou mot de passe incorrect" in r.text


def test_login_sans_csrf_refuse(client, admin):
    r = client.post("/admin/login", data={"identifiant": "gerant", "mot_de_passe": MOT_DE_PASSE})
    assert r.status_code == 403


def test_blocage_apres_5_echecs(client, admin):
    t = jeton(client, "/admin/login")
    codes = [client.post("/admin/login", data={"identifiant": "gerant", "mot_de_passe": "faux", "csrf": t}).status_code
             for _ in range(6)]
    assert codes[-1] == 429
    # Même le bon mot de passe est refusé pendant le blocage.
    assert client.post("/admin/login", data={"identifiant": "gerant", "mot_de_passe": MOT_DE_PASSE,
                                             "csrf": t}).status_code == 429


def test_connexion_et_tableau_de_bord(connecte):
    r = connecte.get("/admin/")
    assert r.status_code == 200 and "Administration" in r.text
    assert r.headers["cache-control"] == "no-store"


def test_modifier_tarif_visible_sur_le_site(connecte, db):
    pid = db.query(Prestation).first().id
    r = connecte.post(f"/admin/tarifs/{pid}", data={"montant_dh": "399", "note": "Prix test",
                                                    "csrf": jeton(connecte, "/admin/")}, follow_redirects=False)
    assert r.status_code == 303
    assert "399 DH" in connecte.get("/").text


def test_tarif_invalide_refuse(connecte, db):
    p = db.query(Prestation).first()
    avant = p.tarif.montant_dh
    for valeur in ["-5", "0", "abc", "99999", ""]:
        connecte.post(f"/admin/tarifs/{p.id}", data={"montant_dh": valeur, "csrf": jeton(connecte, "/admin/")})
    db.refresh(p.tarif)
    assert p.tarif.montant_dh == avant


def test_tarif_sans_csrf_refuse(connecte, db):
    pid = db.query(Prestation).first().id
    assert connecte.post(f"/admin/tarifs/{pid}", data={"montant_dh": "1"}).status_code == 403


def test_modifier_horaire(connecte, db):
    h = db.query(Horaire).filter_by(jour="Samedi").one()
    connecte.post(f"/admin/horaires/{h.id}", data={"ouverture": "09:00", "fermeture": "12:00",
                                                   "csrf": jeton(connecte, "/admin/")})
    db.refresh(h)
    assert (h.ouverture, h.fermeture) == ("09:00", "12:00")


def test_horaire_invalide_refuse(connecte, db):
    h = db.query(Horaire).filter_by(jour="Lundi").one()
    connecte.post(f"/admin/horaires/{h.id}", data={"ouverture": "25:99", "fermeture": "18:00",
                                                   "csrf": jeton(connecte, "/admin/")})
    connecte.post(f"/admin/horaires/{h.id}", data={"ouverture": "18:00", "fermeture": "09:00",
                                                   "csrf": jeton(connecte, "/admin/")})
    db.refresh(h)
    assert h.ouverture == "08:30"


def test_lire_et_supprimer_message(connecte, db):
    db.add(Message(nom="A", telephone="0612345678", contenu="bonjour bonjour"))
    db.commit()
    mid = db.query(Message).one().id
    connecte.post(f"/admin/messages/{mid}/lu", data={"csrf": jeton(connecte, "/admin/")})
    db.expire_all()
    assert db.get(Message, mid).lu is True
    connecte.post(f"/admin/messages/{mid}/supprimer", data={"csrf": jeton(connecte, "/admin/")})
    db.expire_all()
    assert db.get(Message, mid) is None


def test_deconnexion(connecte):
    connecte.post("/admin/logout", data={"csrf": jeton(connecte, "/admin/")})
    assert connecte.get("/admin/", follow_redirects=False).status_code == 303


def test_compte_supprime_perd_l_acces(connecte, db):
    db.query(Administrateur).delete()
    db.commit()
    assert connecte.get("/admin/", follow_redirects=False).status_code == 303


def test_hachage_argon2():
    h = hacher_mot_de_passe("mot-de-passe-long-1")
    assert h.startswith("$argon2id$") and "mot-de-passe" not in h
    assert verifier_mot_de_passe(h, "mot-de-passe-long-1")
    assert not verifier_mot_de_passe(h, "autre")
    assert not verifier_mot_de_passe(None, "autre")


def test_force_mot_de_passe():
    assert not mot_de_passe_assez_fort("court") and mot_de_passe_assez_fort("x" * 12)
