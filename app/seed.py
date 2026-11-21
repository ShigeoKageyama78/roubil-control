"""Données initiales de la base.

TARIFS : recopiés de l'affiche officielle « TARIFICATION – Réseau de visite technique des
véhicules » du centre (tarifs TTC en dirhams, réseau SGS / Aman'Auto). À re-vérifier à chaque
changement de tarif : le dirigeant les modifie ensuite depuis l'espace d'administration.

HORAIRES : valeurs D'EXEMPLE (absentes de l'affiche) à corriger depuis l'administration.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Horaire, Message, Prestation, Tarif

# Ordre d'affichage des colonnes et des lignes de la grille.
TRANCHES = ["Moins de 8 CV", "8 à 10 CV", "11 à 14 CV", "15 CV et plus"]
CATEGORIES = ["Véhicule léger", "Véhicule inférieur à 15 000 kg", "Véhicule supérieur à 15 000 kg", "Autocar"]
RESULTATS = ["Favorable", "Défavorable"]

# (nom, description, {catégorie: (montants « favorable » par tranche, montant « défavorable »)})
_PERIODIQUE = {
    "Véhicule léger": ([350, 370, 390, 420], 240),
    "Véhicule inférieur à 15 000 kg": ([530, 550, 570, 600], 420),
    "Véhicule supérieur à 15 000 kg": ([590, 610, 630, 660], 480),
    "Autocar": ([590, 610, 630, 660], 480),
}
_COMPLEMENTAIRE = {
    "Véhicule léger": ([194, 214, 234, 264], 84),
    "Véhicule inférieur à 15 000 kg": ([254, 274, 294, 324], 144),
    "Véhicule supérieur à 15 000 kg": ([278, 298, 318, 348], 168),
    "Autocar": ([278, 298, 318, 348], 168),
}
_MUTATION = {
    "Véhicule léger": ([300, 320, 340, 370], 240),
    "Véhicule inférieur à 15 000 kg": ([480, 500, 520, 550], 420),
    "Véhicule supérieur à 15 000 kg": ([540, 560, 580, 610], 480),
    "Autocar": ([540, 560, 580, 610], 480),
}

PRESTATIONS = [
    ("Visite technique périodique",
     "Le contrôle obligatoire de votre véhicule : freinage, direction, suspension, éclairage, "
     "pneumatiques, pollution et carrosserie.", _PERIODIQUE),
    ("Visite complémentaire",
     "La contre-visite : après réparation des défauts relevés, nous revérifions les points concernés.",
     _COMPLEMENTAIRE),
    ("Visite mutation",
     "Le contrôle demandé lors d'un changement de propriétaire du véhicule.", _MUTATION),
    ("Visite technique volontaire",
     "Un contrôle fait à votre initiative, par exemple avant d'acheter ou de vendre un véhicule.", _MUTATION),
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
        for ordre, (nom, description, grille) in enumerate(PRESTATIONS, start=1):
            prestation = Prestation(nom=nom, description=description, ordre=ordre)
            for categorie, (favorables, defavorable) in grille.items():
                for tranche, montant in zip(TRANCHES, favorables):
                    prestation.tarifs.append(Tarif(categorie=categorie, tranche_cv=tranche,
                                                   resultat="Favorable", montant_dh=montant))
                for tranche in TRANCHES:  # le tarif « défavorable » ne dépend pas de la puissance
                    prestation.tarifs.append(Tarif(categorie=categorie, tranche_cv=tranche,
                                                   resultat="Défavorable", montant_dh=defavorable))
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
