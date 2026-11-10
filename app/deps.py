"""Dépendances partagées par les routes (injection de dépendances FastAPI)."""
from collections.abc import Iterator

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Administrateur


def get_db(request: Request) -> Iterator[Session]:
    """Ouvre une session de base de données pour la durée d'une requête, puis la ferme."""
    with request.app.state.session_factory() as db:
        yield db


def exiger_admin(request: Request) -> int:
    """Protège les pages d'administration (OWASP A01 : contrôle d'accès).

    Si personne n'est connecté, on redirige vers la page de connexion.
    On revérifie aussi en base que le compte existe encore : un compte supprimé perd
    immédiatement l'accès, même avec un cookie de session encore valide.
    """
    admin_id = request.session.get("admin_id")
    if admin_id is not None:
        with request.app.state.session_factory() as db:
            if db.scalar(select(Administrateur.id).where(Administrateur.id == admin_id)):
                return admin_id
        request.session.clear()
    raise HTTPException(status_code=303, headers={"Location": "/admin/login"})
