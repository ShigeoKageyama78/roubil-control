"""Briques de sécurité : mots de passe, CSRF, limitation de débit, en-têtes HTTP.

Chaque mécanisme répond à un risque du Top 10 OWASP (voir docs/securite.md).
"""
import hmac
import secrets
import time
from collections import defaultdict, deque

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from starlette.requests import Request

# --------------------------------------------------------------------------- #
# 1. Mots de passe (OWASP A02 : défaillances cryptographiques)
# --------------------------------------------------------------------------- #
# Argon2id : algorithme recommandé par l'OWASP. Il est volontairement lent et
# gourmand en mémoire, ce qui rend les attaques par force brute très coûteuses.
_hasher = PasswordHasher()

# Empreinte « factice » : sert à faire le même travail de calcul quand l'identifiant
# n'existe pas. Sans cela, un login inconnu répondrait plus vite qu'un login connu
# et permettrait de deviner quels comptes existent (attaque par temps de réponse).
_EMPREINTE_FACTICE = _hasher.hash("mot-de-passe-factice-pour-egaliser-le-temps")


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    return _hasher.hash(mot_de_passe)


def verifier_mot_de_passe(empreinte: str | None, mot_de_passe: str) -> bool:
    """Vérifie un mot de passe. Si `empreinte` est None (compte inconnu), on calcule
    quand même une vérification factice avant de répondre « faux »."""
    try:
        return _hasher.verify(empreinte or _EMPREINTE_FACTICE, mot_de_passe) and empreinte is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def mot_de_passe_assez_fort(mot_de_passe: str) -> bool:
    """Règle minimale : 12 caractères. La longueur compte plus que la complexité
    (recommandation NIST SP 800-63B)."""
    return len(mot_de_passe) >= 12


# --------------------------------------------------------------------------- #
# 2. Protection CSRF (OWASP A01 : contrôle d'accès défaillant)
# --------------------------------------------------------------------------- #
# Attaque visée : un site malveillant qui force le navigateur d'un administrateur
# connecté à envoyer un formulaire vers notre site. Parade : chaque formulaire
# contient un jeton secret, lié à la session, que l'attaquant ne peut pas deviner.
def jeton_csrf(request: Request) -> str:
    if "csrf" not in request.session:
        request.session["csrf"] = secrets.token_urlsafe(32)
    return request.session["csrf"]


def csrf_valide(request: Request, jeton_soumis: str | None) -> bool:
    attendu = request.session.get("csrf")
    if not attendu or not jeton_soumis:
        return False
    # compare_digest : comparaison en temps constant (pas de fuite par le temps de réponse)
    return hmac.compare_digest(attendu, jeton_soumis)


# --------------------------------------------------------------------------- #
# 3. Limitation de débit (OWASP A07 : défaillances d'authentification)
# --------------------------------------------------------------------------- #
class LimiteurDebit:
    """Fenêtre glissante : au plus `maximum` requêtes par `fenetre` secondes et par clé.

    Limite connue : l'état est gardé en mémoire d'UN processus. Avec plusieurs
    processus ou serveurs, il faudrait un stockage partagé (Redis) ou une limitation
    au niveau du reverse proxy. Documenté dans docs/securite.md.
    """

    def __init__(self, maximum: int, fenetre: int):
        self.maximum = maximum
        self.fenetre = fenetre
        self._evenements: dict[str, deque[float]] = defaultdict(deque)

    def autoriser(self, cle: str) -> bool:
        """Enregistre une tentative et dit si elle est autorisée."""
        maintenant = time.monotonic()
        file = self._evenements[cle]
        # On retire les tentatives sorties de la fenêtre
        while file and maintenant - file[0] > self.fenetre:
            file.popleft()
        if len(file) >= self.maximum:
            return False
        file.append(maintenant)
        return True

    def reinitialiser(self) -> None:
        self._evenements.clear()


# --------------------------------------------------------------------------- #
# 4. En-têtes HTTP de sécurité (OWASP A05 : mauvaise configuration)
# --------------------------------------------------------------------------- #
EN_TETES_SECURITE = {
    # Politique de contenu : seules nos propres ressources sont chargées. Aucun script,
    # style ou police tiers : limite fortement l'impact d'une éventuelle faille XSS.
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
        "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",  # le navigateur ne « devine » pas les types de fichiers
    "X-Frame-Options": "DENY",  # interdit d'afficher le site dans une iframe (clickjacking)
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}

# HSTS (forcer HTTPS) n'est ajouté que si le cookie est configuré « secure »,
# c'est-à-dire quand le site est réellement servi en HTTPS.
EN_TETE_HSTS = {"Strict-Transport-Security": "max-age=31536000; includeSubDomains"}


def ip_client(request: Request) -> str:
    """Adresse IP du client. Derrière un reverse proxy, lancer uvicorn avec
    --proxy-headers pour que request.client reflète la vraie IP."""
    return request.client.host if request.client else "inconnue"
