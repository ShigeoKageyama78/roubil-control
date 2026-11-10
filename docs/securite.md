# Sécurité

Correspondance avec l'OWASP Top 10 (2021). « Testé » renvoie à un test automatique dans `tests/`.

| Risque | Mesure | Où | Testé |
|---|---|---|---|
| A01 Contrôle d'accès | Dépendance `exiger_admin` sur toutes les routes admin ; le compte est revérifié en base | `deps.py` | oui |
| A02 Cryptographie | Mots de passe hachés Argon2id (jamais en clair) ; cookie de session signé, HttpOnly, SameSite=Lax, Secure en production ; HSTS | `security.py`, `main.py` | oui (hachage) |
| A03 Injection | SQLAlchemy (requêtes paramétrées) ; échappement automatique Jinja2 ; `textContent` côté JS ; en-têtes e-mail non alimentés par l'utilisateur | modèles, templates, `notifications.py` | oui |
| A04 Conception | Limitation de débit (contact, connexion) ; champ piège anti-robots ; minimisation et purge à 90 jours | `security.py`, `seed.py` | oui |
| A05 Mauvaise configuration | CSP stricte `default-src 'self'`, X-Frame-Options, nosniff, Referrer-Policy, Permissions-Policy ; `/docs` désactivé ; page 404 sans détail technique ; conteneur non-root | `main.py`, `Dockerfile` | oui |
| A06 Composants vulnérables | Versions figées ; `pip-audit` en CI | `requirements.txt`, CI | oui (CI) |
| A07 Authentification | Anti force brute (5 essais / 15 min), message d'erreur identique, temps de réponse équilibré, session renouvelée à la connexion (fixation), mot de passe ≥ 12 caractères | `admin.py` | oui |
| A08 Intégrité | CSRF : jeton lié à la session sur tous les POST | `security.py` | oui |
| A09 Journalisation | Échecs d'envoi d'e-mail journalisés (pas de journal d'audit complet) | `notifications.py` | partiel |
| A10 SSRF | Non concerné : le serveur n'appelle aucune URL fournie par l'utilisateur | — | — |

## Limites assumées
- Limiteur de débit en mémoire (un seul processus) et basé sur l'IP ; derrière un proxy, configurer l'IP réelle.
- Pas de double authentification ni de journal d'audit des actions admin.
- Aucun test d'intrusion externe n'a été réalisé : seuls des tests automatiques et bandit / pip-audit.
