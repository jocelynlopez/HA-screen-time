# Proposal

## Why

Le rapport hebdomadaire n'existe que sous forme de notification : elle disparaît quand on la ferme, et l'enfant ne peut pas voir ce qu'on lui a donné ou retiré. Le parent n'a pas non plus de moyen de voir, en milieu de semaine, ce que donnera le prochain bilan du lundi (nouveau crédit, notes à venir, capital).

## What Changes

- **Capteur « Rapport »** sur l'appareil de l'enfant, dont les attributs contiennent du texte Markdown à afficher dans une carte Markdown du tableau de bord : `last_report` (dernier rapport du lundi), `history` (rapports précédents) et `forecast` (prévision).
- **Historique des rapports du lundi** : chaque rapport diffusé le lundi est enregistré avec l'état (les 52 derniers, soit un an), donc toujours disponible, même après un redémarrage. La prévision, elle, n'est pas conservée : elle est recalculée à la demande.
- **Rapport prévisionnel** : à tout moment, le portefeuille calcule, sans rien modifier, le bilan comme si le prochain lundi 00h00 était arrivé (nouveau crédit hebdomadaire, notes pas encore comptées, capital et temps disponible attendus). Il reprend aussi les mouvements manuels et la consommation automatique de la semaine en cours : l'enfant y voit le temps donné ou retiré. Il est recalculé au démarrage, après chaque mouvement et à chaque changement du capteur de notes.
- **README** : exemple de carte Markdown (fr et en).

## Capabilities

### New Capabilities
Aucune.

### Modified Capabilities
- `screen-time-wallet`: prévision du prochain bilan sans effet sur l'état.
- `ha-integration`: capteur « Rapport », conservation du dernier rapport, mise à jour de la prévision.

## Impact

- `engine/wallet.py` (prévision), `report.py` (titre de prévision, rapport sans source), `runtime.py` (rendu, enregistrement du dernier rapport, mise à jour de la prévision), `sensor.py` (capteur), `__init__.py` (chargement du dernier rapport), traductions fr et en, `README.md`.
- L'état enregistré gagne une clé facultative `reports` (comme `source_entity`) : aucune migration, version mineure `0.7.0`.

## Hors périmètre

- Une carte personnalisée ou une jauge (change `weekly-gauge`).
- Prévoir la consommation à venir de la semaine : la prévision suppose que rien ne change d'ici lundi.
- Conserver l'historique des prévisions.
