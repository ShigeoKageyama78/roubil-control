# Plan de tests

Outil : pytest, client HTTP de test FastAPI, base SQLite en mémoire recréée pour chaque test.

| Fichier | Contenu |
|---|---|
| `test_public.py` | pages, API JSON, en-têtes, 404, contact valide / invalide / sans CSRF / honeypot / limite de débit, XSS, injection SQL |
| `test_admin.py` | accès sans connexion, connexion, blocage après 5 échecs, modification tarifs / horaires (valides et invalides), messages, déconnexion, Argon2 |
| `test_validation.py` | validation des champs, purge de rétention |
| `test_cli_notifications.py` | commande create-admin, e-mail (pas d'injection d'en-tête, panne SMTP) |

Résultat au 10/11/2026 : 44 tests réussis, couverture 96 % (`pytest --cov=app`) ; bandit : aucun problème ; pip-audit : aucune vulnérabilité connue.

Non couvert : rendu visuel sur différents navigateurs (vérifié manuellement sous Chromium uniquement), construction de l'image Docker, envoi réel d'e-mails.
