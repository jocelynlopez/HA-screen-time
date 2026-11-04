# Proposal

## Why

L'intégration `screen_time_wallet` fonctionne, mais sans source de données : chaque lundi elle applique le crédit de repli (240 min) et un crédit de semaine nul. Les moyennes et les notes existent déjà dans Home Assistant, publiées par l'intégration `ecole_directe` (HACS, `hacf-fr/hass-ecoledirecte`) : un capteur de notes et un capteur de moyenne par matière. Ce change lit ces capteurs pour que le bilan du lundi utilise les vraies données, sans écrire de connexion à l'API d'EcoleDirecte.

## What Changes

- **Source EcoleDirecte** : une option permet de choisir le capteur de notes de l'enfant (par exemple `sensor.ed_mael_lopez_notes`). Les notes sont lues dans son attribut `notes` ; les moyennes par matière sont **découvertes automatiquement** parmi les capteurs de la même intégration (ceux qui portent les attributs `Nom` et `Code`), leur état étant la moyenne.
- **Reconnaissance des matières tolérante** : la comparaison ignore aussi la ponctuation et les espaces, pour que le capteur de sport (`ed.physique & sport.`) soit reconnu comme `ED PHYSIQUE & SPORT`.
- **Activation de la source** : au moment où un capteur de notes est choisi ou changé, les notes déjà visibles sont mémorisées sans effet et le crédit hebdomadaire est remplacé par le crédit initial calculé sur les vraies moyennes.
- **Robustesse** : si la source n'est pas prête (démarrage de HA, capteur indisponible), nouvelles tentatives après quelques minutes, puis au déclenchement quotidien ; une notification persistante signale une source indisponible quand un bilan est en retard. L'intégration se charge après `ecole_directe`.
- **Cœur** : nouvelle opération d'activation d'une source dans le portefeuille.

## Capabilities

### New Capabilities
- `ecoledirecte-source`: lecture des notes et des moyennes par matière dans les capteurs de l'intégration EcoleDirecte, et traduction en données du bilan.

### Modified Capabilities
- `grade-conversion`: la reconnaissance du nom de matière ignore aussi la ponctuation et les espaces.
- `screen-time-wallet`: ajout de l'activation d'une source.
- `ha-integration`: option du capteur de notes, activation de la source, nouvelles tentatives, notification de source indisponible, ordre de chargement.

## Impact

- Nouveau module `custom_components/screen_time_wallet/ecole_directe_source.py` ; `config_flow.py`, `__init__.py`, `runtime.py`, `options.py`, `manifest.json` et les traductions sont étendus ; `engine/config.py` (normalisation) et `engine/wallet.py` (activation) évoluent.
- Aucune dépendance Python ajoutée ; aucun appel réseau : seules les entités de HA sont lues.
- `README.md` : configuration de la source et conseil d'augmenter « Notes maximum affichées » dans l'intégration EcoleDirecte.

## Hors périmètre

- Connexion à l'API d'EcoleDirecte et authentification (portées par l'intégration `ecole_directe`).
- Sélection manuelle de chaque capteur de moyenne.
- Capteur de moyenne générale d'EcoleDirecte (la moyenne générale reste calculée par le portefeuille).
- Mesure de la consommation (change suivant).
