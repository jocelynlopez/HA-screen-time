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

Sans source de notes, le bilan applique le crédit de repli (240 min par défaut). Avec la **source EcoleDirecte**
(voir plus bas), il utilise les vraies moyennes et les vraies notes. La mesure de la consommation arrive dans une
version suivante.

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
  notification, capteurs de temps d'écran.
- **Matières et multiplicateurs** : ajouter, modifier ou supprimer une matière (nom tel qu'écrit par EcoleDirecte).

Une matière inconnue ou une note rejetée déclenche une notification.

## Source EcoleDirecte

L'intégration lit les entités de l'intégration Home Assistant
[`ecole_directe`](https://github.com/hacf-fr/hass-ecoledirecte) ; elle ne se connecte jamais elle-même à EcoleDirecte.

1. Installer et configurer `ecole_directe` pour l'enfant.
2. Dans les options du portefeuille, *Paramètres de calcul*, choisir le **capteur de notes** (par exemple
   `sensor.ed_mael_lopez_notes`).
3. Les **moyennes par matière** sont découvertes automatiquement : ce sont les capteurs de la même intégration qui ont
   les attributs `Nom` et `Code`, leur état étant la moyenne.

Au premier choix du capteur (ou à son changement), les notes déjà visibles sont **mémorisées sans effet** et le crédit
hebdomadaire est calculé sur les moyennes actuelles. Seules les notes saisies ensuite comptent.

À savoir :

- Les noms de matières sont reconnus sans tenir compte de la casse, des accents, de la ponctuation ni des espaces
  (`ed.physique & sport.` est le sport). Une matière absente de la table est signalée par une notification.
- Dans l'intégration EcoleDirecte, **augmenter « Notes maximum affichées »** (15 par défaut) : le portefeuille ne voit
  que les notes affichées par ce capteur.
- Si la source est indisponible quand un bilan est dû (démarrage de Home Assistant, capteur absent), le bilan est
  retenté 3 fois à 5 minutes d'intervalle, puis chaque nuit ; une notification persistante signale la panne et disparaît
  au bilan réussi.

## Capteurs de temps d'écran

Le portefeuille peut débiter automatiquement le temps réellement utilisé, à partir des capteurs de l'intégration
[`microsoft_family_safety`](https://github.com/noiwid/HAFamilySafety) (par exemple `sensor.pc_mael_screen_time`). Il
ne l'installe ni ne la configure.

1. Installer et configurer `microsoft_family_safety`.
2. Dans les options du portefeuille, *Paramètres de calcul*, choisir un ou plusieurs **capteurs de temps d'écran** :
   prendre celui de l'**appareil** (le PC), pas le total de l'enfant, qui additionne aussi les autres appareils.

Fonctionnement :

- Le relevé d'un capteur est le temps utilisé dans la journée : son attribut `total_seconds` divisé par 60, ou à défaut
  son état en minutes.
- À chaque nouveau relevé, la **différence avec le relevé de référence** est consommée (crédit hebdomadaire d'abord,
  puis capital notes). Les fractions de minute sont reportées au relevé suivant ; plusieurs capteurs s'additionnent.
- Au **premier relevé** d'un capteur (choix dans les options), rien n'est facturé : l'usage déjà écoulé ne compte pas.
- Le compteur repart de zéro chaque nuit. Un **changement de jour** (attribut `date`) ou, à défaut, une **baisse** du
  compteur vaut remise à zéro : le nouveau relevé est alors la consommation depuis la remise à zéro.
- Les relevés de référence sont enregistrés avec l'état : au redémarrage, la différence survenue pendant l'arrêt est
  consommée, sans perdre ni doubler de minute.
- Les consommations automatiques d'un même capteur dans la même journée forment **une seule ligne du journal**.
- Un capteur « indisponible » ou « inconnu » est ignoré.

Limites : le temps disponible suit le rythme du capteur (5 minutes par défaut) ; l'usage entre le dernier relevé de la
veille et minuit n'est pas compté ; un relevé numérique erroné (un 0 isolé) serait compté comme un nouvel usage au retour
de la vraie valeur : le journal le montre et le service `screen_time_wallet.adjust` le corrige.

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
