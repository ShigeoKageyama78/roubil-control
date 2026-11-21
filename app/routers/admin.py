"""Espace d'administration : connexion, tarifs, horaires, messages.

Règles appliquées à CHAQUE route de ce fichier :
- accès réservé aux administrateurs connectés (dépendance `exiger_admin`) ;
- toute action qui modifie des données est un POST protégé par un jeton CSRF ;
- les données reçues sont validées côté serveur avant d'être enregistrées.
"""
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.deps import exiger_admin, get_db
from app.models import Administrateur, Horaire, Message, Prestation
from app.security import csrf_valide, ip_client, jeton_csrf, verifier_mot_de_passe
from app.routers.public import construire_grille
from app.seed import TRANCHES
from app.validation import nettoyer, valider_heure, valider_montant

router = APIRouter(prefix="/admin")


def _page(request: Request, nom: str, status_code: int = 200, **contexte):
    contexte.setdefault("csrf", jeton_csrf(request))
    contexte["settings"] = request.app.state.settings
    return request.app.state.templates.TemplateResponse(
        request, f"admin/{nom}", contexte, status_code=status_code
    )


def _verifier_csrf(request: Request, jeton: str) -> None:
    if not csrf_valide(request, jeton):
        raise HTTPException(status_code=403, detail="Jeton de sécurité invalide.")


# --- Connexion / déconnexion -----------------------------------------------------------

@router.get("/login")
def login_page(request: Request):
    if request.session.get("admin_id") is not None:
        return RedirectResponse("/admin/", status_code=303)
    return _page(request, "login.html", erreur="")


@router.post("/login")
def login(
    request: Request,
    db: Session = Depends(get_db),
    identifiant: str = Form(""),
    mot_de_passe: str = Form(""),
    csrf: str = Form(""),
):
    _verifier_csrf(request, csrf)

    # Anti force brute : 5 essais par 15 minutes et par adresse IP.
    if not request.app.state.limiteur_login.autoriser(ip_client(request)):
        return _page(request, "login.html", status_code=429,
                     erreur="Trop de tentatives. Réessayez dans 15 minutes.")

    admin = db.scalar(select(Administrateur).where(Administrateur.identifiant == nettoyer(identifiant)))
    # verifier_mot_de_passe prend le même temps que le compte existe ou non
    # (empreinte factice), pour ne pas révéler quels identifiants existent.
    if not verifier_mot_de_passe(admin.mot_de_passe_hash if admin else None, mot_de_passe):
        return _page(request, "login.html", status_code=401, erreur="Identifiant ou mot de passe incorrect.")

    # Fixation de session : on vide l'ancienne session avant d'y inscrire l'identité,
    # ce qui invalide tout cookie qu'un attaquant aurait pu faire adopter à la victime.
    request.session.clear()
    request.session["admin_id"] = admin.id
    return RedirectResponse("/admin/", status_code=303)


@router.post("/logout")
def logout(request: Request, csrf: str = Form("")):
    _verifier_csrf(request, csrf)
    request.session.clear()
    return RedirectResponse("/admin/login", status_code=303)


# --- Tableau de bord ---------------------------------------------------------------------

@router.get("/")
def tableau_de_bord(request: Request, _: int = Depends(exiger_admin), db: Session = Depends(get_db)):
    messages = db.scalars(select(Message).order_by(Message.cree_le.desc())).all()
    prestations = db.scalars(
        select(Prestation).options(selectinload(Prestation.tarifs)).order_by(Prestation.ordre)
    ).all()
    horaires = db.scalars(select(Horaire).order_by(Horaire.ordre)).all()
    return _page(
        request, "dashboard.html",
        messages=messages, prestations=prestations, horaires=horaires, tranches=TRANCHES,
        grilles={p.id: construire_grille(p) for p in prestations},
        non_lus=sum(1 for m in messages if not m.lu),
        info=request.session.pop("info", ""), erreur=request.session.pop("erreur", ""),
    )


# --- Tarifs --------------------------------------------------------------------------------

@router.post("/tarifs/{prestation_id}")
async def modifier_tarifs(prestation_id: int, request: Request, _: int = Depends(exiger_admin),
                          db: Session = Depends(get_db)):
    """Enregistre en une fois tous les tarifs d'une prestation (les champs sont nommés t_<id>)."""
    formulaire = await request.form()
    _verifier_csrf(request, str(formulaire.get("csrf", "")))
    prestation = db.get(Prestation, prestation_id)
    if prestation is None:
        raise HTTPException(status_code=404)

    # On valide TOUT avant de modifier quoi que ce soit : si un montant est faux, rien n'est enregistré.
    nouveaux = {}
    for tarif in prestation.tarifs:
        montant = valider_montant(str(formulaire.get(f"t_{tarif.id}", "")))
        if montant is None:
            request.session["erreur"] = (
                f"Montant invalide pour « {tarif.categorie}, {tarif.tranche_cv}, {tarif.resultat} » : "
                "entrez un nombre entier entre 1 et 10 000. Rien n'a été enregistré.")
            return RedirectResponse("/admin/", status_code=303)
        nouveaux[tarif.id] = montant
    for tarif in prestation.tarifs:
        tarif.montant_dh = nouveaux[tarif.id]
    db.commit()
    request.session["info"] = f"Tarifs « {prestation.nom} » mis à jour."
    return RedirectResponse("/admin/", status_code=303)


# --- Horaires ------------------------------------------------------------------------------

@router.post("/horaires/{horaire_id}")
def modifier_horaire(
    horaire_id: int, request: Request, _: int = Depends(exiger_admin), db: Session = Depends(get_db),
    ferme: str = Form(""), ouverture: str = Form(""), fermeture: str = Form(""), csrf: str = Form(""),
):
    _verifier_csrf(request, csrf)
    horaire = db.get(Horaire, horaire_id)
    if horaire is None:
        raise HTTPException(status_code=404)
    est_ferme = ferme == "on"
    if not est_ferme:
        if not (valider_heure(ouverture) and valider_heure(fermeture)) or ouverture >= fermeture:
            request.session["erreur"] = "Horaires invalides : format HH:MM, ouverture avant fermeture."
            return RedirectResponse("/admin/", status_code=303)
    horaire.ferme = est_ferme
    horaire.ouverture = "" if est_ferme else ouverture.strip()
    horaire.fermeture = "" if est_ferme else fermeture.strip()
    db.commit()
    request.session["info"] = f"Horaires du {horaire.jour.lower()} mis à jour."
    return RedirectResponse("/admin/", status_code=303)


# --- Messages ------------------------------------------------------------------------------

@router.post("/messages/{message_id}/lu")
def marquer_lu(
    message_id: int, request: Request, _: int = Depends(exiger_admin),
    db: Session = Depends(get_db), csrf: str = Form(""),
):
    _verifier_csrf(request, csrf)
    message = db.get(Message, message_id)
    if message is None:
        raise HTTPException(status_code=404)
    message.lu = True
    db.commit()
    return RedirectResponse("/admin/#messages", status_code=303)


@router.post("/messages/{message_id}/supprimer")
def supprimer_message(
    message_id: int, request: Request, _: int = Depends(exiger_admin),
    db: Session = Depends(get_db), csrf: str = Form(""),
):
    _verifier_csrf(request, csrf)
    message = db.get(Message, message_id)
    if message is None:
        raise HTTPException(status_code=404)
    db.delete(message)
    db.commit()
    request.session["info"] = "Message supprimé."
    return RedirectResponse("/admin/#messages", status_code=303)
