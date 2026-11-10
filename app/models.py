"""Modèles de données (tables SQL).

Schéma (voir docs/conception.md pour le MCD complet) :

    Prestation 1 ──── 1 Tarif        un tarif par prestation
    Horaire                          une ligne par jour de la semaine
    Message                          messages envoyés via le formulaire de contact
    Administrateur                   comptes autorisés à se connecter à l'espace admin
"""
from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def maintenant() -> datetime:
    """Date/heure UTC « consciente » du fuseau (évite les ambiguïtés)."""
    return datetime.now(timezone.utc)


class Prestation(Base):
    __tablename__ = "prestation"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(80), unique=True)
    description: Mapped[str] = mapped_column(Text)
    ordre: Mapped[int] = mapped_column(Integer, default=0)

    tarif: Mapped["Tarif"] = relationship(
        back_populates="prestation", uselist=False, cascade="all, delete-orphan"
    )


class Tarif(Base):
    __tablename__ = "tarif"
    # Contrainte au niveau de la base : un prix ne peut pas être négatif ou nul.
    __table_args__ = (CheckConstraint("montant_dh > 0", name="ck_tarif_positif"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    prestation_id: Mapped[int] = mapped_column(
        ForeignKey("prestation.id", ondelete="CASCADE"), unique=True
    )
    libelle_vehicule: Mapped[str] = mapped_column(String(80))  # ex. « Voiture particulière »
    montant_dh: Mapped[int] = mapped_column(Integer)
    note: Mapped[str] = mapped_column(String(160), default="")

    prestation: Mapped[Prestation] = relationship(back_populates="tarif")


class Horaire(Base):
    __tablename__ = "horaire"

    id: Mapped[int] = mapped_column(primary_key=True)
    jour: Mapped[str] = mapped_column(String(20), unique=True)  # « Lundi », « Mardi »...
    ordre: Mapped[int] = mapped_column(Integer)  # 1 = lundi ... 7 = dimanche
    ferme: Mapped[bool] = mapped_column(Boolean, default=False)
    ouverture: Mapped[str] = mapped_column(String(5), default="")  # « 08:30 »
    fermeture: Mapped[str] = mapped_column(String(5), default="")  # « 18:30 »


class Message(Base):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(80))
    telephone: Mapped[str] = mapped_column(String(25))
    contenu: Mapped[str] = mapped_column(Text)
    lu: Mapped[bool] = mapped_column(Boolean, default=False)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=maintenant)


class Administrateur(Base):
    __tablename__ = "administrateur"

    id: Mapped[int] = mapped_column(primary_key=True)
    identifiant: Mapped[str] = mapped_column(String(40), unique=True)
    # On ne stocke JAMAIS le mot de passe, seulement son empreinte Argon2id.
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255))
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=maintenant)
