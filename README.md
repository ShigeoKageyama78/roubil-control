# ROUBIL CONTROLE – site du centre de contrôle technique

Site web du centre ROUBIL CONTROLE (Bouskoura, Casablanca) : présentation des prestations, tarifs, horaires,
simulateur de tarif, formulaire de contact et espace d'administration.

Projet réalisé par Bilal Hmaili (Bachelor Cybersécurité, ESIEE-IT). Le site statique initial a été livré pendant le
stage (01/07–31/08/2026). Le back-end (base SQL, administration, sécurité, tests, Docker, CI) a été développé
**après le stage**, à partir de novembre 2026 (voir `docs/gestion-de-projet.md`).

## Lancer en local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # puis renseigner SECRET_KEY
python -m app.cli create-admin gerant      # crée le compte (mot de passe demandé, 12 caractères minimum)
uvicorn app.main:create_app --factory --reload
```

Site : http://127.0.0.1:8000 · Administration : http://127.0.0.1:8000/admin/login

## Tests et contrôles

```bash
python -m pytest -q --cov=app     # 46 tests
bandit -r app                     # analyse statique de sécurité
pip-audit -r requirements.txt     # vulnérabilités connues des dépendances
```

## Docker

```bash
cp .env.example .env && docker compose up --build
```

L'image est construite automatiquement par l'intégration continue (GitHub Actions) à chaque push. Elle n'a pas encore été déployée sur un serveur.

## Avant toute mise en ligne

- Définir une `SECRET_KEY` longue et aléatoire (`python -c "import secrets; print(secrets.token_urlsafe(48))"`). Sans elle, une clé temporaire est générée et les sessions sont perdues à chaque redémarrage.
- Passer `COOKIE_SECURE=true` (le site doit être servi en HTTPS).
- **Tarifs :** recopiés de l'affiche officielle du centre (`app/seed.py`) ; à re-vérifier si l'affiche change. **Horaires : valeurs d'exemple** (absents de l'affiche), à corriger dans l'espace d'administration.
- **Base existante :** il n'y a pas de migration de schéma. Si vous aviez lancé une ancienne version, supprimez le dossier `data/` (la base sera recréée) puis recréez le compte administrateur.
- Renseigner SMTP_* si l'on veut être prévenu par e-mail (sinon les messages restent visibles dans l'administration).
- Faire valider les mentions de confidentialité (loi 09-08 / CNDP) par le dirigeant.

## Limites connues

- Pas de système de réservation (hors périmètre ; voir backlog).
- Limiteur de débit en mémoire : valable pour un seul processus. Avec plusieurs instances, utiliser Redis.
- Un seul rôle administrateur ; pas de double authentification.
- Pas d'hébergement ni de nom de domaine à ce jour.

## Structure

```
app/            code (main, routers/, models, security, validation, seed, cli)
app/templates/  pages Jinja2 (échappement automatique)
app/static/     CSS et JavaScript (aucune ressource externe)
tests/          tests pytest (base SQLite en mémoire)
docs/           cahier des charges, conception, sécurité, gestion de projet, tests
```
