# Cahier des charges

## Contexte
ROUBIL CONTROLE est un centre de contrôle technique automobile (réseau SGS Maroc) à Bouskoura. Le dirigeant souhaite un site qui présente les prestations et les tarifs, et permette aux clients de le contacter.

## Utilisateurs
- **Visiteur** : automobiliste qui cherche un prix, des horaires, une adresse, ou veut poser une question.
- **Administrateur** : le dirigeant ou son équipe, qui met à jour les informations sans toucher au code.

## Besoins (user stories, priorisation MoSCoW)

| # | En tant que… | Je veux… | Priorité |
|---|---|---|---|
| 1 | visiteur | voir les prestations et leur prix | Must |
| 2 | visiteur | voir les horaires et l'adresse | Must |
| 3 | visiteur | envoyer un message au centre | Must |
| 4 | administrateur | me connecter de façon sécurisée | Must |
| 5 | administrateur | modifier les tarifs et horaires | Must |
| 6 | administrateur | lire et supprimer les messages reçus | Must |
| 7 | visiteur | estimer mon tarif avec un simulateur | Should |
| 8 | visiteur | utiliser le site sur téléphone | Should |
| 9 | administrateur | être prévenu par e-mail | Could |
| 10 | visiteur | réserver un créneau | Won't (cette version) |

## Contraintes
- Données personnelles : loi marocaine 09-08 (CNDP) → minimisation, durée de conservation, information.
- Aucune ressource externe (polices, scripts) : sécurité et confidentialité.
- Budget nul, hébergement non décidé → application simple à déployer (SQLite, Docker).

## Critères d'acceptation (exemples)
- Un message valide apparaît dans l'administration ; un message invalide est refusé avec des erreurs précises.
- Une page d'administration est inaccessible sans connexion.
- Un tarif modifié dans l'administration s'affiche immédiatement sur le site.
