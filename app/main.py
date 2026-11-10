"""Point d'entrée : construit l'application FastAPI.

On utilise une « fabrique » (create_app) plutôt qu'une variable globale : les tests
peuvent ainsi créer une application isolée, avec une base en mémoire et une
configuration à eux. Lancement : « uvicorn app.main:create_app --factory ».
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.engine import Engine
from starlette.middleware.sessions import SessionMiddleware

from app.config import Settings, get_settings
from app.database import Base, creer_engine, creer_session_factory
from app.routers import admin, public
from app.security import EN_TETE_HSTS, EN_TETES_SECURITE, LimiteurDebit
from app.seed import initialiser_donnees, purger_messages_anciens

DOSSIER = Path(__file__).parent


def create_app(settings: Settings | None = None, engine: Engine | None = None) -> FastAPI:
    settings = settings or get_settings()
    engine = engine or creer_engine(settings.database_url)
    session_factory = creer_session_factory(engine)

    @asynccontextmanager
    async def cycle_de_vie(app: FastAPI):
        # Au démarrage : création des tables, données initiales, purge des vieux messages.
        Base.metadata.create_all(engine)
        with session_factory() as db:
            initialiser_donnees(db)
            purger_messages_anciens(db, settings.retention_days)
        yield

    # Pas de documentation automatique exposée (/docs, /openapi.json) : inutile pour un
    # site vitrine et cela réduit la surface d'attaque.
    app = FastAPI(
        title="ROUBIL CONTROLE",
        lifespan=cycle_de_vie,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    # --- État partagé, accessible depuis les routes via request.app.state -------------
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.templates = Jinja2Templates(directory=str(DOSSIER / "templates"))
    # Contact : 5 messages / heure / IP. Connexion admin : 5 essais / 15 min / IP.
    app.state.limiteur_contact = LimiteurDebit(maximum=5, fenetre=3600)
    app.state.limiteur_login = LimiteurDebit(maximum=5, fenetre=900)

    # --- Sessions : cookie signé, HttpOnly, SameSite=Lax, « Secure » en production ----
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie="roubil_session",
        max_age=8 * 3600,
        same_site="lax",
        https_only=settings.cookie_secure,
    )

    # --- En-têtes de sécurité sur TOUTES les réponses ---------------------------------
    @app.middleware("http")
    async def ajouter_en_tetes_securite(request: Request, call_next):
        reponse = await call_next(request)
        for nom, valeur in EN_TETES_SECURITE.items():
            reponse.headers[nom] = valeur
        if settings.cookie_secure:
            for nom, valeur in EN_TETE_HSTS.items():
                reponse.headers[nom] = valeur
        # Les pages d'administration ne doivent jamais être mises en cache.
        if request.url.path.startswith("/admin"):
            reponse.headers["Cache-Control"] = "no-store"
        return reponse

    app.mount("/static", StaticFiles(directory=str(DOSSIER / "static")), name="static")
    app.include_router(public.router)
    app.include_router(admin.router)

    # --- Page 404 personnalisée (sans fuite d'information technique) -------------------
    @app.exception_handler(404)
    async def page_introuvable(request: Request, exc):
        return app.state.templates.TemplateResponse(
            request, "404.html", {"settings": settings}, status_code=404
        )

    return app
