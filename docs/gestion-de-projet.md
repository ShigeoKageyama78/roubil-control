# Gestion de projet

## Deux phases, à distinguer clairement

**Phase 1 – Stage (01/07 → 31/08/2026)** : site vitrine statique (HTML/CSS/JS), livré au dirigeant. Non hébergé.

**Phase 2 – Extension après stage (novembre 2026)** : réponse aux limites constatées après l'évaluation (formulaire non fonctionnel, pas de données, pas de tests ni de documentation de gestion de projet). Réalisée avec l'aide d'un assistant IA (Claude) : le code est commenté pour être relu et expliqué. L'historique git de cette phase commence le 10/11/2026 ; il n'existe pas d'historique git du stage.

## Méthode
Itérations courtes, backlog priorisé (MoSCoW, voir `cahier-des-charges.md`), tableau Kanban (À faire / En cours / Fait), un commit par étape cohérente.

## Backlog et avancement au 10/11/2026

| Étape | Statut |
|---|---|
| Cahier des charges, conception | Fait |
| Back-end, modèles SQL, seed | Fait |
| Formulaire de contact sécurisé | Fait |
| Espace d'administration | Fait |
| Simulateur JavaScript | Fait |
| Tests, bandit, pip-audit | Fait |
| Docker, CI | Écrits ; CI non exécutée (pas encore sur GitHub), image non construite |
| Hébergement, nom de domaine | Non fait (décision du dirigeant) |
| Réservation en ligne | Reporté |

## Risques

| Risque | Probabilité | Impact | Mesure |
|---|---|---|---|
| Tarifs d'exemple pris pour les vrais | Moyenne | Fort | Signalés dans le README et `seed.py` ; à corriger via l'admin avant mise en ligne |
| Faille de sécurité | Moyenne | Fort | Tests, bandit, pip-audit, en-têtes, revue OWASP |
| Perte des messages (SQLite) | Faible | Moyen | Volume Docker ; sauvegarde à prévoir |
| Données personnelles non conformes (09-08) | Moyenne | Moyen | Mention, consentement, purge à 90 jours ; validation à obtenir |
| Code que l'étudiant ne sait pas expliquer | Moyenne | Fort | Code commenté en français, relecture préparée avant la soutenance |

## Rétrospective (10/11/2026)

- **Ce qui a bien fonctionné** : tests écrits en même temps que le code ; en-têtes de sécurité vérifiés par tests ; architecture simple.
- **Ce qui a moins bien fonctionné** : pas de gestion de projet formelle ni de git pendant le stage → corrigé a posteriori, mais non rattrapable pour la phase 1.
- **Corrections apportées par les tests** : voir l'historique git.
- **Pistes** : réservation, Redis pour le limiteur, double authentification, sauvegardes, mise en ligne.
