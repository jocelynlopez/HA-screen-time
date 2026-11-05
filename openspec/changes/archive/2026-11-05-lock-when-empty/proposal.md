# Proposal

## Why

Le portefeuille calcule le temps disponible et le débite, mais ne bloque rien quand il est épuisé : l'utilisateur doit écrire lui-même des automatisations qui verrouillent l'appareil. Ce change fait piloter les interrupteurs de blocage par l'intégration, pour que le temps disponible suffise à décider si l'enfant peut utiliser l'appareil.

## What Changes

- **Interrupteurs de blocage** : deux options permettent de choisir un ou plusieurs interrupteurs (`switch`) à piloter. Les interrupteurs de **verrouillage** (ON = bloqué, comme l'Account Lock de `microsoft_family_safety`) et les interrupteurs d'**autorisation** (OFF = bloqué). Les deux listes sont vides par défaut : dans ce cas rien n'est piloté et l'utilisateur peut verrouiller à la main.
- **Blocage automatique** : quand le temps disponible est inférieur ou égal à 0, le portefeuille met chaque interrupteur à l'état « bloqué » ; quand il redevient positif (recharge du lundi, ajustement, notes), il les remet à l'état « libre ». Tous les interrupteurs choisis sont pilotés ensemble, ce qui bloque toutes les plateformes de l'interrupteur.
- **État imposé** : l'état des interrupteurs est remis en accord avec le temps disponible à chaque relevé d'un capteur de temps d'écran, au démarrage, après un bilan, une consommation ou un ajustement. Un basculement manuel contraire est donc annulé ; pour donner du temps, on utilise l'ajustement.
- **Échecs signalés** : un basculement qui échoue est signalé par une notification persistante et réessayé au relevé suivant ; elle disparaît au succès.
- **Bilan dû** : tant qu'un bilan du lundi est dû (source en panne), l'état des interrupteurs ne change pas.

## Capabilities

### New Capabilities
Aucune.

### Modified Capabilities
- `ha-integration`: options des interrupteurs de blocage, blocage et déblocage automatiques, notification d'échec.

## Impact

- `const.py` et `options.py` (deux options), `config_flow.py` (deux sélecteurs d'interrupteurs et validation), `runtime.py` (calcul de l'état voulu, basculement, notification d'échec), traductions fr et en, `report.py` (texte de la notification d'échec), `README.md`.
- Le cœur (`engine/`) ne change pas. Aucune dépendance Python ; les interrupteurs sont pilotés par les services Home Assistant `switch.turn_on` et `switch.turn_off`.

## Hors périmètre

- Avertissement avant la coupure (« il reste 10 minutes »).
- Pilotage d'entités qui ne sont pas des `switch`, et intégration Family Link (elle fournira ses propres interrupteurs).
- Gestion du délai de l'API Microsoft (environ une minute) ou de ses pannes, au-delà du signalement et de la nouvelle tentative.
