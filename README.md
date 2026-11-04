# Screen Time Wallet — portefeuille de minutes de temps d'écran

Intégration personnalisée pour Home Assistant : un **portefeuille de minutes de temps d'écran par enfant**, alimenté
chaque lundi à partir des moyennes et des notes scolaires.

## Fonctionnement

- Chaque lundi à 00h00, un **bilan** verse :
  - un **crédit hebdomadaire** issu de la moyenne générale, remis à sa valeur chaque semaine (non cumulable) ;
  - un **crédit de semaine** issu de la moyenne des notes de la semaine écoulée, ajouté au **capital notes**, qui se
    cumule et peut être négatif.
- Le **temps disponible** est la somme des deux. La consommation débite d'abord le crédit hebdomadaire.
- Un **rapport** détaille le calcul chaque lundi (notification persistante, et service `notify` optionnel).

Cette version est la base : sans source de notes, le bilan applique le crédit de repli (240 min par défaut).
La lecture des notes EcoleDirecte et la mesure de la consommation arrivent dans les versions suivantes.

## Installation

- **HACS** : *Dépôts personnalisés* → ajouter ce dépôt (catégorie *Intégration*), télécharger, redémarrer Home Assistant.
- **Manuelle** (Home Assistant Container compris) : copier le dossier `custom_components/screen_time_wallet` dans
  `<config>/custom_components/`, puis redémarrer Home Assistant.

Ensuite : *Paramètres → Appareils et services → Ajouter une intégration → Screen Time Wallet* et saisir le prénom de
l'enfant (une entrée par enfant).

## Options

*Configurer* sur l'entrée :

- **Paramètres de calcul** : temps maximal par semaine (heures, pour 20/20 partout), part des notes (%), note pivot,
  poids minimal, nombre minimal de matières, crédit de repli, notes non significatives, rapport hebdomadaire, service de
  notification.
- **Matières et multiplicateurs** : ajouter, modifier ou supprimer une matière (nom tel qu'écrit par EcoleDirecte).

Une matière inconnue ou une note rejetée déclenche une notification.

## Entités

Pour chaque enfant : *Temps disponible*, *Crédit hebdomadaire*, *Capital notes* (en minutes) et *Dernier bilan*
(date, crédit initial, crédit de semaine et 20 derniers mouvements en attributs).

## Services

- `screen_time_wallet.consume` : consomme des minutes (`minutes` > 0, `reason` optionnel), crédit hebdomadaire d'abord.
- `screen_time_wallet.adjust` : ajuste le capital notes (`minutes` positif ou négatif, non nul, `reason` optionnel).

Ils ciblent un capteur du portefeuille. L'identifiant dépend de la langue de Home Assistant (en français
`sensor.mael_temps_disponible`, en anglais `sensor.mael_available_time`), par exemple :

```yaml
action: screen_time_wallet.consume
target:
  entity_id: sensor.mael_temps_disponible
data:
  minutes: 45
  reason: jeu console
```

## Développement

```bash
uv sync
uv run pytest
```

Le projet suit [OpenSpec](https://github.com/Fission-AI/OpenSpec) : les exigences sont dans `openspec/specs/` et chaque
test déclare l'exigence qu'il vérifie avec le marqueur `requirement`.
