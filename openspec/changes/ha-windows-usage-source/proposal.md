# Proposal

## Why

Le portefeuille se recharge chaque lundi, mais rien ne le débite quand l'enfant utilise réellement l'ordinateur : le service `consume` doit être appelé à la main. L'intégration Home Assistant `microsoft_family_safety` (HACS, `noiwid/HAFamilySafety`) publie le temps d'écran du jour, par appareil et par enfant, en minutes. Ce change lit ces capteurs et débite automatiquement le portefeuille de l'écart entre deux relevés, pour que le temps disponible reflète l'usage réel du PC Windows.

## What Changes

- **Capteurs de temps d'écran** : une option permet de choisir un ou plusieurs capteurs (par exemple `sensor.{appareil}_screen_time`). Leur état est le nombre de minutes utilisées *aujourd'hui*.
- **Consommation automatique** : à chaque nouveau relevé, la différence avec le relevé précédent est consommée (crédit hebdomadaire d'abord, puis capital notes). Plusieurs capteurs s'additionnent.
- **Compteur journalier robuste** : le compteur repart de zéro à un moment que le README de l'intégration ne précise pas. Une baisse du compteur est donc traitée comme une remise à zéro (le nouveau relevé est alors la consommation depuis la remise à zéro), sans supposer d'heure.
- **Premier relevé sans débit** : quand un capteur est choisi, son relevé actuel devient la référence ; l'usage déjà écoulé n'est pas facturé.
- **Relevés conservés** : les relevés de référence sont enregistrés avec l'état, pour qu'un redémarrage de Home Assistant ne perde ni ne double aucune minute.
- **Journal lisible** : les consommations automatiques d'un même capteur dans la même journée sont regroupées en un seul mouvement.

## Capabilities

### New Capabilities
- `screen-time-usage`: calcul de la consommation entre deux relevés d'un compteur journalier (premier relevé, remise à zéro, relevé invalide, minutes fractionnaires).

### Modified Capabilities
- `screen-time-wallet`: regroupement des consommations automatiques dans le journal.
- `ha-integration`: option des capteurs de temps d'écran, consommation automatique, relevés conservés.

## Impact

- Nouveau module `custom_components/screen_time_wallet/engine/usage.py` (calcul pur) ; `runtime.py`, `__init__.py`, `config_flow.py`, `const.py`, `options.py` et les traductions sont étendus ; `engine/wallet.py` gagne le regroupement.
- Aucune dépendance Python ; aucun appel réseau : seules les entités de HA sont lues.
- `README.md` : configuration des capteurs de temps d'écran.

## Hors périmètre

- Verrouiller ou déverrouiller le PC quand le temps disponible est épuisé (automatisation de l'utilisateur sur le capteur « Temps disponible », avec l'interrupteur de verrouillage de l'intégration Family Safety).
- Temps du téléphone (Family Link) et mesure par prise connectée.
- Installation et configuration de l'intégration `microsoft_family_safety`.
- Lecture du compteur par plateforme (Windows, Xbox, mobile) : on lit les capteurs que l'utilisateur choisit.
