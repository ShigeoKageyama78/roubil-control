"""Données initiales de la base.

ATTENTION : les tarifs et horaires ci-dessous sont des valeurs D'EXEMPLE, calées sur
les fourchettes de prix publiées au Maroc en 2026 (AutoActu : 370-400 DH pour une voiture,
400-450 DH pour un utilitaire léger, 200-250 DH pour une moto). Ce ne sont pas les tarifs
réels du centre : le dirigeant doit les corriger depuis l'espace d'administration.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Horaire, Message, Prestation, Tarif

PRESTATIONS = [
    ("Visite technique périodique",
     "Le contrôle obligatoire de votre véhicule : freinage, direction, suspension, éclairage, "
     "pneumatiques, pollution et état de la carrosserie.",
     "Voiture particulière", 380, ""),
    ("Contre-visite",
     "Après réparation d'un défaut relevé, nous revérifions uniquement les points concernés, "
     "dans le délai indiqué sur votre procès-verbal.",
     "Après une visite refusée", 150, "Dans le délai réglementaire"),
    ("Véhicule utilitaire léger",
     "Fourgons et utilitaires jusqu'à 3,5 tonnes, avec les vérifications propres à leur usage.",
     "Jusqu'à 3,5 tonnes", 420, ""),
    ("Contrôle avant achat ou vente",
     "Un état des lieux complet du véhicule, utile pour vendre en confiance ou pour savoir "
     "ce que vous achetez.",
     "Contrôle volontaire", 400, "Rapport détaillé remis au client"),
    ("Deux et trois-roues",
     "Motocycles et tricycles à moteur, contrôlés sur la ligne dédiée du centre.",
     "Motocycle et tricycle", 220, ""),
]

HORAIRES = [
    ("Lundi", 1, False, "08:30", "18:30"),
    ("Mardi", 2, False, "08:30", "18:30"),
    ("Mercredi", 3, False, "08:30", "18:30"),
    ("Jeudi", 4, False, "08:30", "18:30"),
    ("Vendredi", 5, False, "08:30", "18:30"),
    ("Samedi", 6, False, "08:30", "13:00"),
    ("Dimanche", 7, True, "", ""),
]


def initialiser_donnees(db: Session) -> None:
    """Remplit les tables vides. Ne touche pas aux données déjà présentes."""
    if db.scalar(select(Prestation.id).limit(1)) is None:
        for ordre, (nom, description, vehicule, montant, note) in enumerate(PRESTATIONS, start=1):
            prestation = Prestation(nom=nom, description=description, ordre=ordre)
            prestation.tarif = Tarif(libelle_vehicule=vehicule, montant_dh=montant, note=note)
            db.add(prestation)

    if db.scalar(select(Horaire.id).limit(1)) is None:
        for jour, ordre, ferme, ouverture, fermeture in HORAIRES:
            db.add(Horaire(jour=jour, ordre=ordre, ferme=ferme, ouverture=ouverture, fermeture=fermeture))

    db.commit()


def purger_messages_anciens(db: Session, jours: int) -> int:
    """Supprime les messages de plus de `jours` jours (minimisation : on ne garde pas
    des données personnelles plus longtemps que nécessaire). Retourne le nombre supprimé."""
    limite = datetime.now(timezone.utc) - timedelta(days=jours)
    resultat = db.execute(delete(Message).where(Message.cree_le < limite))
    db.commit()
    return resultat.rowcount or 0
