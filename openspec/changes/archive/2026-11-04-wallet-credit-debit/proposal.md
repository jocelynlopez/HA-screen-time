# Proposal

## Why

Le temps d'écran de l'enfant doit dépendre de ses résultats scolaires, mais un portefeuille alimenté uniquement par les notes reste vide quand il y a peu de contrôles. Il faut donc un budget de base hebdomadaire, ajusté à la hausse ou à la baisse par les notes. Cette première étape ne porte que sur la logique métier, sans connexion à EcoleDirecte : les notes arrivent sous forme de données.

## What Changes

- Un portefeuille de minutes de temps d'écran avec un solde en minutes entières, qui peut être négatif.
- Une allocation hebdomadaire de 240 minutes (4 h), créditée chaque lundi à 00h00.
- Une conversion de chaque note en minutes créditées ou débitées : `minutes = taux de base × multiplicateur de matière × (note sur 20 − 12) × coefficient`, arrondi à l'entier le plus proche.
- Le taux de base (15 min/point), la note pivot (12/20), l'allocation hebdomadaire et les multiplicateurs de matière sont des paramètres de configuration, modifiables sans toucher à la logique.
- Le solde se reporte d'une semaine à l'autre, qu'il soit positif ou négatif.
- Une note déjà traitée (même identifiant) n'est jamais comptée deux fois.

## Capabilities

### New Capabilities
- `grade-conversion`: calcul des minutes créditées ou débitées pour une note (barème, pivot, coefficient, multiplicateur de matière, arrondi).
- `screen-time-wallet`: solde de minutes, allocation hebdomadaire, report du solde, application des notes au solde sans double traitement.

### Modified Capabilities

Aucune (premier change du projet).

## Impact

- Nouveau code Python dans `src/portefeuille_minutes/` (logique métier pure, sans I/O).
- Nouveaux tests pytest, chacun rattaché à l'exigence de la spec qu'il vérifie.
- Aucune dépendance externe ajoutée. Aucun accès réseau, ni à EcoleDirecte ni à un autre service.

## Hors périmètre

- Connexion à l'API EcoleDirecte et récupération des notes.
- Persistance du solde (fichier, base de données) et interface utilisateur.
- Contrôle effectif du temps d'écran sur les appareils.
- Opération manuelle de crédit ou de débit parental.
