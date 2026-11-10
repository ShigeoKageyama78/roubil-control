"""Connexion à la base de données (SQLAlchemy 2.x)."""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    """Classe de base de tous les modèles (tables)."""


def creer_engine(database_url: str) -> Engine:
    """Crée le moteur de base de données.

    - SQLite : on crée le dossier du fichier si besoin. Pour une base en mémoire
      (tests), StaticPool garde une seule connexion, sinon chaque connexion verrait
      une base vide différente.
    - Autres bases (PostgreSQL...) : configuration standard.
    """
    if database_url.startswith("sqlite"):
        if ":memory:" in database_url:
            return create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        chemin = database_url.replace("sqlite:///", "", 1)
        Path(chemin).parent.mkdir(parents=True, exist_ok=True)
        return create_engine(database_url, connect_args={"check_same_thread": False})
    return create_engine(database_url, pool_pre_ping=True)


def creer_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
