"""Configuration de l'application, lue depuis les variables d'environnement.

Principe (12-factor) : aucun secret n'est écrit dans le code. Tout ce qui change
entre le poste de développement et la production passe par l'environnement.
"""
import os
import secrets
from dataclasses import dataclass


def _bool(valeur: str | None, defaut: bool = False) -> bool:
    if valeur is None:
        return defaut
    return valeur.strip().lower() in {"1", "true", "oui", "yes"}


@dataclass(frozen=True)
class Settings:
    secret_key: str
    database_url: str
    cookie_secure: bool
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    notify_to: str
    retention_days: int


def get_settings() -> Settings:
    """Construit la configuration à chaque appel (pratique pour les tests)."""
    # Sans SECRET_KEY définie, on génère une clé aléatoire : l'application démarre,
    # mais les sessions sont perdues au redémarrage. Acceptable en développement,
    # à éviter en production (d'où l'avertissement dans le README).
    secret = os.getenv("SECRET_KEY") or secrets.token_urlsafe(48)
    return Settings(
        secret_key=secret,
        database_url=os.getenv("DATABASE_URL", "sqlite:///./data/roubil.sqlite3"),
        cookie_secure=_bool(os.getenv("COOKIE_SECURE")),
        smtp_host=os.getenv("SMTP_HOST", ""),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_user=os.getenv("SMTP_USER", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        notify_to=os.getenv("NOTIFY_TO", ""),
        retention_days=int(os.getenv("RETENTION_DAYS", "90")),
    )
