from app.models import Message
from tests.conftest import jeton

VALIDE = {"nom": "Karim B.", "telephone": "+212 6 12 34 56 78", "contenu": "Quels documents apporter ?"}


def test_accueil_affiche_les_tarifs_de_la_base(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Visite technique périodique" in r.text and "DH" in r.text


def test_api_tarifs_json(client):
    r = client.get("/api/tarifs")
    assert r.status_code == 200
    donnees = r.json()
    assert len(donnees) == 5 and all(isinstance(t["montant_dh"], int) for t in donnees)
    assert sum(t["est_contre_visite"] for t in donnees) == 1


def test_en_tetes_de_securite(client):
    h = client.get("/").headers
    assert "default-src 'self'" in h["content-security-policy"]
    assert h["x-frame-options"] == "DENY"
    assert h["x-content-type-options"] == "nosniff"
    assert "strict-transport-security" not in h  # HSTS seulement en HTTPS


def test_docs_automatiques_desactivees(client):
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_page_404_personnalisee(client):
    r = client.get("/nimporte-quoi")
    assert r.status_code == 404 and "Page introuvable" in r.text and "Traceback" not in r.text


def test_sante_robots_sitemap_confidentialite(client):
    assert client.get("/sante").json() == {"statut": "ok"}
    assert "Disallow: /admin" in client.get("/robots.txt").text
    assert "<urlset" in client.get("/sitemap.xml").text
    assert "09-08" in client.get("/confidentialite").text


def test_contact_valide_enregistre_le_message(client, db):
    r = client.post("/contact", data={**VALIDE, "csrf": jeton(client)}, follow_redirects=False)
    assert r.status_code == 303
    assert db.query(Message).count() == 1
    assert "bien été envoyé" in client.get("/").text


def test_contact_sans_csrf_refuse(client, db):
    assert client.post("/contact", data=VALIDE).status_code == 403
    assert db.query(Message).count() == 0


def test_contact_mauvais_csrf_refuse(client):
    jeton(client)
    assert client.post("/contact", data={**VALIDE, "csrf": "faux"}).status_code == 403


def test_contact_invalide_renvoie_les_erreurs(client, db):
    r = client.post("/contact", data={"nom": "", "telephone": "12", "contenu": "court", "csrf": jeton(client)})
    assert r.status_code == 422
    assert db.query(Message).count() == 0
    assert r.text.count('class="erreur"') >= 3


def test_honeypot_ignore_les_robots(client, db):
    r = client.post("/contact", data={**VALIDE, "site_web": "http://spam", "csrf": jeton(client)},
                    follow_redirects=False)
    assert r.status_code == 303 and db.query(Message).count() == 0


def test_limitation_de_debit(client):
    t = jeton(client)
    codes = [client.post("/contact", data={**VALIDE, "csrf": t}, follow_redirects=False).status_code
             for _ in range(6)]
    assert codes[:5] == [303] * 5 and codes[5] == 429


def test_xss_echappe_a_l_affichage(client, connecte):
    connecte.post("/contact", data={"nom": "<script>alert(1)</script>", "telephone": "0612345678",
                                    "contenu": "<img src=x onerror=alert(1)> message", "csrf": jeton(connecte)})
    page = connecte.get("/admin/").text
    assert "<script>alert(1)</script>" not in page and "&lt;script&gt;" in page


def test_injection_sql_traitee_comme_du_texte(client, db):
    client.post("/contact", data={"nom": "Robert'); DROP TABLE message;--", "telephone": "0612345678",
                                  "contenu": "message assez long ' OR '1'='1", "csrf": jeton(client)})
    assert db.query(Message).count() == 1  # la table existe toujours, la valeur est stockée telle quelle
