# Proposal

## Why

Le rapport hebdomadaire du lundi détaille le calcul des crédits mais ne liste pas les mouvements manuels de la semaine, et les justifications saisies avec les actions `adjust` et `consume` n'y apparaissent donc pas. Les trois éléments ajoutés en v0.5.0 (entité « Minutes » et deux boutons) ne permettent pas de saisir une raison. Un script avec fenêtre de saisie (minutes et raison) fonctionne mieux ; ce change le fournit sous forme de blueprints et rend les justifications traçables dans le rapport.

## What Changes

- **Origine des mouvements** : le journal marque les consommations automatiques ; les ajustements et consommations manuels (actions) restent sans origine. Un regroupement ne concerne que des mouvements automatiques.
- **Rapport hebdomadaire** : une section « Mouvements manuels de la semaine » liste, pour la semaine écoulée, chaque ajustement et chaque consommation manuelle (date, variation du temps disponible, motif), puis le total consommé automatiquement par capteur, pour rapprocher le solde.
- **Blueprints de script** : le dépôt fournit deux blueprints, « ajouter du temps » (action `adjust`) et « retirer du temps » (action `consume`), qui demandent le capteur du portefeuille, des minutes et une raison obligatoire dans une fenêtre. Le README propose leur import en un clic. Une intégration ne peut pas créer d'entité script elle-même : le blueprint est le moyen le plus proche.
- **Retrait** (non rétrocompatible) : l'entité numérique « Minutes » et les boutons « Ajouter du temps » et « Retirer du temps » de la v0.5.0 sont supprimés, et leurs entités orphelines sont retirées du registre au démarrage.

## Capabilities

### New Capabilities
Aucune.

### Modified Capabilities
- `screen-time-wallet`: origine des mouvements du journal, mouvements de la semaine dans le compte rendu du bilan.
- `ha-integration`: section des mouvements manuels dans le rapport, retrait des commandes de la v0.5.0 et de leurs entités, blueprints de script.

## Impact

- `engine/wallet.py` (origine du mouvement, mouvements de la semaine dans `Report`), `report.py` (section du rapport), `runtime.py` et `__init__.py` (retrait de la valeur des minutes, nettoyage du registre), suppression de `number.py`, `button.py`, des constantes et traductions associées et du test des commandes, nouveaux fichiers `blueprints/script/screen_time_wallet/add_time.yaml` et `remove_time.yaml`, `README.md`.
- Aucune dépendance ; l'état enregistré garde son format (le champ `detail` des mouvements existe déjà).
- Version mineure `0.6.0` : le retrait des entités n'est pas rétrocompatible.

## Hors périmètre

- Rendre la raison obligatoire dans les actions `adjust` et `consume`.
- Une entité qui ouvre la fenêtre de saisie : une entité ne peut pas ouvrir de fenêtre dans Home Assistant.
- Un motif propre à chaque capteur de temps d'écran pour les consommations automatiques.
