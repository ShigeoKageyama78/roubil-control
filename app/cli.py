"""Commandes d'administration en ligne de commande.

    python -m app.cli create-admin <identifiant>   crée (ou remplace le mot de passe d')un compte
    python -m app.cli purge                         supprime les messages plus vieux que RETENTION_DAYS

Le mot de passe est demandé de façon masquée (getpass) : il n'apparaît ni à l'écran,
ni dans l'historique du terminal, ni dans un fichier.
"""
import argparse
import getpass
import sys

from sqlalchemy import select

from app.config import get_settings
from app.database import Base, creer_engine, creer_session_factory
from app.models import Administrateur
from app.security import hacher_mot_de_passe, mot_de_passe_assez_fort
from app.seed import initialiser_donnees, purger_messages_anciens


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    sous = parser.add_subparsers(dest="commande", required=True)
    admin = sous.add_parser("create-admin", help="créer un compte administrateur")
    admin.add_argument("identifiant")
    sous.add_parser("purge", help="purger les anciens messages")
    args = parser.parse_args(argv)

    settings = get_settings()
    engine = creer_engine(settings.database_url)
    Base.metadata.create_all(engine)
    with creer_session_factory(engine)() as db:
        initialiser_donnees(db)
        if args.commande == "purge":
            print(f"{purger_messages_anciens(db, settings.retention_days)} message(s) supprimé(s).")
            return 0

        mdp = getpass.getpass("Mot de passe (12 caractères minimum) : ")
        if not mot_de_passe_assez_fort(mdp):
            print("Mot de passe trop court.", file=sys.stderr)
            return 1
        if mdp != getpass.getpass("Confirmez : "):
            print("Les deux saisies diffèrent.", file=sys.stderr)
            return 1
        compte = db.scalar(select(Administrateur).where(Administrateur.identifiant == args.identifiant))
        if compte is None:
            compte = Administrateur(identifiant=args.identifiant, mot_de_passe_hash="")
            db.add(compte)
        compte.mot_de_passe_hash = hacher_mot_de_passe(mdp)
        db.commit()
        print(f"Compte « {args.identifiant} » enregistré.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
