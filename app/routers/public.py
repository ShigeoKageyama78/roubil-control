"""Routes publiques : page d'accueil, API des tarifs, formulaire de contact, pages légales."""
from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.deps import get_db
from app.models import Horaire, Message, Prestation
from app.notifications import notifier_nouveau_message
from app.security import csrf_valide, ip_client, jeton_csrf
from app.validation import valider_contact

router = APIRouter()


def _donnees_accueil(db: Session) -> dict:
    """Charge depuis la base tout ce que la page d'accueil affiche."""
    prestations = db.scalars(
        select(Prestation).options(joinedload(Prestation.tarif)).order_by(Prestation.ordre)
    ).all()
    horaires = db.scalars(select(Horaire).order_by(Horaire.ordre)).all()
    return {"prestations": prestations, "horaires": horaires}


def _rendre_accueil(request: Request, db: Session, status_code: int = 200, **extra) -> Response:
    contexte = {
        "settings": request.app.state.settings,
        "csrf": jeton_csrf(request),
        "erreurs": {},
        "valeurs": {},
        "envoye": False,
        **_donnees_accueil(db),
        **extra,
    }
    return request.app.state.templates.TemplateResponse(
        request, "index.html", contexte, status_code=status_code
    )


@router.get("/")
def accueil(request: Request, db: Session = Depends(get_db)):
    # « envoye » est posé par la redirection qui suit un envoi réussi (voir /contact).
    envoye = request.session.pop("message_envoye", False)
    return _rendre_accueil(request, db, envoye=envoye)


@router.get("/api/tarifs")
def api_tarifs(db: Session = Depends(get_db)):
    """Tarifs au format JSON : utilisés par le simulateur de tarif (static/js/simulateur.js)."""
    prestations = db.scalars(
        select(Prestation).options(joinedload(Prestation.tarif)).order_by(Prestation.ordre)
    ).all()
    return JSONResponse(
        [
            {
                "id": p.id,
                "nom": p.nom,
                "vehicule": p.tarif.libelle_vehicule,
                "montant_dh": p.tarif.montant_dh,
                "note": p.tarif.note,
                "est_contre_visite": p.nom.lower().startswith("contre-visite"),
            }
            for p in prestations
            if p.tarif
        ]
    )


@router.post("/contact")
def contact(
    request: Request,
    taches: BackgroundTasks,
    db: Session = Depends(get_db),
    nom: str = Form(""),
    telephone: str = Form(""),
    contenu: str = Form(""),
    site_web: str = Form(""),  # champ « piège » (voir ci-dessous)
    csrf: str = Form(""),
):
    settings = request.app.state.settings

    # 1. Jeton CSRF : sans lui, la requête ne vient pas de notre propre formulaire.
    if not csrf_valide(request, csrf):
        raise HTTPException(status_code=403, detail="Jeton de sécurité invalide.")

    # 2. Limitation de débit : au plus 5 messages par heure et par adresse IP.
    if not request.app.state.limiteur_contact.autoriser(ip_client(request)):
        return _rendre_accueil(
            request, db, status_code=429,
            erreurs={"general": "Trop de messages envoyés. Réessayez dans une heure ou appelez le centre."},
        )

    # 3. Champ piège (« honeypot ») : invisible pour un humain (caché en CSS), mais les
    #    robots de spam remplissent tous les champs. S'il est rempli, on fait semblant
    #    d'accepter sans rien enregistrer, pour ne pas renseigner le robot.
    if site_web.strip():
        request.session["message_envoye"] = True
        return RedirectResponse("/#contact", status_code=303)

    # 4. Validation côté serveur.
    donnees, erreurs = valider_contact(nom, telephone, contenu)
    if erreurs:
        return _rendre_accueil(
            request, db, status_code=422, erreurs=erreurs,
            valeurs={"nom": nom, "telephone": telephone, "contenu": contenu},
        )

    # 5. Enregistrement. SQLAlchemy utilise des requêtes paramétrées : les valeurs ne
    #    sont jamais collées dans le texte SQL, donc pas d'injection SQL possible.
    db.add(Message(nom=donnees["nom"], telephone=donnees["telephone"], contenu=donnees["contenu"]))
    db.commit()

    # 6. Notification e-mail en arrière-plan (ne retarde pas la réponse au visiteur).
    taches.add_task(notifier_nouveau_message, settings, donnees["nom"], donnees["telephone"], donnees["contenu"])

    # Redirection après POST (« Post/Redirect/Get ») : un rafraîchissement de page
    # ne renvoie pas le message une seconde fois.
    request.session["message_envoye"] = True
    return RedirectResponse("/#contact", status_code=303)


@router.get("/confidentialite")
def confidentialite(request: Request):
    return request.app.state.templates.TemplateResponse(
        request, "confidentialite.html", {"settings": request.app.state.settings}
    )


@router.get("/sante")
def sante(db: Session = Depends(get_db)):
    """Point de contrôle pour Docker / l'hébergeur : vérifie que la base répond."""
    db.execute(select(1))
    return {"statut": "ok"}


@router.get("/robots.txt", response_class=PlainTextResponse)
def robots():
    return "User-agent: *\nDisallow: /admin\nSitemap: /sitemap.xml\n"


@router.get("/sitemap.xml")
def sitemap(request: Request):
    base = str(request.base_url).rstrip("/")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{base}/</loc></url><url><loc>{base}/confidentialite</loc></url></urlset>"
    )
    return Response(content=xml, media_type="application/xml")
