"""Validation des données saisies par les visiteurs.

Règle d'or (OWASP A03 : injection) : on ne fait JAMAIS confiance à ce que le
navigateur envoie. Tout est validé côté serveur, même si le HTML contient déjà
des attributs `required` ou `maxlength` (qu'un attaquant peut contourner).
"""
import re

# Chiffres, espaces, +, -, ., parenthèses : couvre « 0661 07 48 29 » et « +212 661-074829 »
_TEL = re.compile(r"^[0-9 +().\-]{8,20}$")


def nettoyer(texte: str | None) -> str:
    """Supprime les espaces autour et les caractères de contrôle (sauf retour à la ligne)."""
    if texte is None:
        return ""
    propre = "".join(c for c in texte if c in "\n\t" or c.isprintable())
    return propre.strip()


def valider_contact(nom: str | None, telephone: str | None, contenu: str | None):
    """Retourne (donnees_propres, erreurs). `erreurs` est vide si tout est valide."""
    nom, telephone, contenu = nettoyer(nom), nettoyer(telephone), nettoyer(contenu)
    erreurs: dict[str, str] = {}

    if not 2 <= len(nom) <= 80:
        erreurs["nom"] = "Indiquez votre nom (2 à 80 caractères)."
    if not _TEL.match(telephone) or sum(c.isdigit() for c in telephone) < 8:
        erreurs["telephone"] = "Indiquez un numéro de téléphone valide."
    if not 10 <= len(contenu) <= 1000:
        erreurs["contenu"] = "Votre message doit contenir entre 10 et 1000 caractères."

    return {"nom": nom, "telephone": telephone, "contenu": contenu}, erreurs


def valider_montant(valeur: str | None) -> int | None:
    """Convertit un montant saisi en entier de dirhams (1 à 10 000), sinon None."""
    try:
        montant = int((valeur or "").strip())
    except ValueError:
        return None
    return montant if 1 <= montant <= 10_000 else None


_HEURE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def valider_heure(valeur: str | None) -> bool:
    return bool(_HEURE.match((valeur or "").strip()))
