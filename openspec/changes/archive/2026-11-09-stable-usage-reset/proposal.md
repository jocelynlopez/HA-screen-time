# Proposal

## Why

Sur le portefeuille de Mael, la consommation automatique de l'ordinateur a été comptée 77 minutes de trop en trois jours (169 minutes comptées pour 92 réellement consommées), à cause de deux recomptages :

- **Minuit** : l'attribut `date` du capteur d'appareil Family Safety est la date du jour de Home Assistant, pas celle des données. À minuit il change alors que le total reste celui de la veille jusqu'à la prochaine interrogation. La règle « changement de jour = remise à zéro » recompte alors tout le total de la veille (−40 min observées).
- **Relevé transitoirement bas** : toute baisse du compteur le même jour vaut remise à zéro et le relevé entier est consommé. Une baisse passagère puis un retour à la valeur normale recompte le relevé bas (−36 min observées). Le capteur Family Safety renvoie 0 quand les données de l'appareil manquent, ce qui peut produire ce relevé bas (hypothèse, non vérifiée sur le relevé lui-même).

Par ailleurs, le rapport hebdomadaire coupe la liste des mouvements manuels à 30 lignes (« … et 4 autre(s) »).

## What Changes

- **Changement de jour avec relevé identique** : le relevé est jugé périmé. Rien n'est consommé, la référence garde ses minutes et prend le nouveau jour, et la baisse suivante est acceptée tout de suite comme remise à zéro.
- **Baisse le même jour** : le premier relevé plus bas n'est pas consommé, il rend la référence « suspecte ». Un relevé qui remonte au niveau de la référence ou au-dessus annule le doute ; un second relevé plus bas confirme la remise à zéro.
- Une baisse sans date (référence ou relevé) reste une remise à zéro immédiate.
- **Rapport hebdomadaire** : tous les mouvements manuels de la semaine sont listés, sans limite de lignes.

## Capabilities

### New Capabilities
Aucune.

### Modified Capabilities
- `screen-time-usage`: remise à zéro du compteur.
- `screen-time-wallet`: mouvements de la semaine dans le compte rendu.

## Impact

- `engine/usage.py` (`Baseline.suspect`, `consumed_since`), `report.py` (suppression de `MAX_MANUAL_LINES`), tests existants de la remise à zéro.
- Le format enregistré gagne un champ optionnel `suspect` dans les relevés de référence ; un état ancien reste lisible. Version `0.9.1`.

## Hors périmètre

- Corriger rétroactivement le solde de Mael : à faire avec l'action `adjust` (+77, motif « correction décompte »).
- Réparer le capteur Family Safety lui-même.
