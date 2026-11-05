# Proposal

## Why

À l'activation de la source, toutes les notes visibles sont mémorisées « sans effet » pour ne pas compter l'historique de l'année. Quand l'activation a lieu en milieu de semaine, les notes déjà saisies cette semaine-là (par exemple le français du 02/11 et les arts plastiques du 03/11, activation le 05/11) sont aussi écartées : elles ne comptent dans aucun bilan, et la prévision n'affiche aucune ligne de note. Le portefeuille déjà activé de l'utilisateur est dans ce cas.

## What Changes

- **Activation en cours de semaine** : à l'activation, seules les notes datées d'avant le lundi 00h00 de la semaine en cours sont mémorisées sans effet. Celles de la semaine en cours restent à compter au prochain bilan.
- **Action `screen_time_wallet.recount_week`** : action d'entité (comme `consume` et `adjust`) qui rend à compter les notes de la semaine en cours déjà mémorisées, pour corriger un portefeuille déjà activé. Elle relit la source, retire ces notes des notes vues, enregistre l'état et rafraîchit la prévision. Elle ne touche ni au crédit hebdomadaire ni au capital ni au journal.
- **README** : l'action et le moment où l'utiliser (fr et en).

## Capabilities

### New Capabilities
Aucune.

### Modified Capabilities
- `screen-time-wallet`: activation d'une source, recomptage des notes de la semaine.
- `ha-integration`: activation de la source, action de recomptage.

## Impact

- `engine/wallet.py` (activation, recomptage), `runtime.py` (action), `sensor.py` (enregistrement de l'action), `services.yaml`, traductions fr et en, `README.md`, tests de l'activation existants (leurs notes sont datées de la semaine en cours).
- Le format de l'état enregistré ne change pas. Version mineure `0.9.0`.

## Hors périmètre

- Réactiver la source en changeant de capteur : cela réécrirait aussi le crédit hebdomadaire.
- Recompter les notes de semaines précédentes.
- Détecter automatiquement une activation incomplète sur un portefeuille existant (migration).
