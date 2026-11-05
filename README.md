# Screen Time Wallet

🇬🇧 English · [🇫🇷 Français](#-français)

A custom integration for Home Assistant: a **screen time wallet of minutes per child**, topped up every Monday from
school averages and grades, and debited automatically by the time actually spent on the computer.

## How it works

- Every Monday at 00:00, a **settlement** adds:
  - a **weekly credit** derived from the general average, reset to its value each week (it does not accumulate);
  - a **week credit** derived from the grades of the past week, added to the **grades capital**, which accumulates and
    can go negative.
- The **available time** is the sum of both. Consumption debits the weekly credit first.
- A **report** explains the week to the child every Monday (persistent notification, plus an optional `notify` service),
  with the minutes each grade brought:

  ```
  Your time this week (Monday 09/11/2026):
  • Carried over from previous weeks: +145 min
  • MATHEMATIQUES 15.2/20: +138 min
  • FRANCAIS 7/20: -415 min
  • Overall average bonus (15.80): +227 min
  Available time: 95 min
  ```

  The *overall average bonus* is the weekly credit (from the overall average) plus the part of the grades credit that
  this week's grades do not cover (all of it when there is no grade). The lines always add up to the available time. The
  report also lists the **manual movements of the past week** (date, signed minutes and reason of each adjustment or manual
  consumption, up to 30 lines) and the time consumed automatically by each sensor, so the balance can be traced.

Without a grades source, the settlement applies the fallback credit (240 min by default). With the **EcoleDirecte
source** (see below), it uses the real averages and grades. With **screen time sensors** (see below), consumption is
debited automatically.

## Installation

- **HACS** (recommended): *Custom repositories* → add `https://github.com/jocelynlopez/HA-screen-time` (category
  *Integration*), download, restart Home Assistant.
- **Manual** (Home Assistant Container included): copy the `custom_components/screen_time_wallet` folder to
  `<config>/custom_components/`, then restart Home Assistant.

Then: *Settings → Devices & services → Add integration → Screen Time Wallet* and enter the child's first name (one
entry per child).

## Options

*Configure* on the entry:

- **Calculation settings**: maximum time per week (hours, for 20/20 everywhere), share of the week's grades (%), pivot
  grade, minimum weight, minimum number of subjects, fallback credit, non-significant grades, weekly report,
  notification service, EcoleDirecte notes sensor, screen time sensors, lock and allow switches.
- **Subjects and multipliers**: add, edit or remove a subject (name as written by EcoleDirecte), or tick **Detect the
  subjects of the source** to add at once those the source publishes. The window shows the **current table** (one line
  per subject with its multiplier, in alphabetical order) above the form.

A rejected grade triggers a notification.

### Subjects are detected automatically

When a source is activated and before each settlement, every subject published by the source (the per-subject average
sensors, with or without an average, and the subjects of the grades) that is not yet in the table is **added with
multiplier 1** and used in that calculation. A notification names the added subjects.

- Set the multiplier of an added subject in *Subjects and multipliers*; **0 excludes it** from the calculation (useful
  for non-academic items such as a class-life entry). A subject already in the table, even at 0, is never modified.
- Deleting a subject that the source still publishes adds it back with multiplier 1 at the next detection: use 0 to
  exclude it instead.
- **Detect the subjects of the source** (tick it in *Subjects and multipliers*, the subject name is then optional) runs
  the same detection on demand and shows the result in the window, without any notification. The weekly credit is not
  recomputed: the added subjects count from the next settlement. The result message and the notification of added
  subjects both list the current table.

## EcoleDirecte source

The integration reads the entities of the Home Assistant
[`ecole_directe`](https://github.com/hacf-fr/hass-ecoledirecte) integration; it never connects to EcoleDirecte itself.

1. Install and configure `ecole_directe` for the child.
2. In the wallet options, *Calculation settings*, choose the **notes sensor** (for example
   `sensor.ed_mael_lopez_notes`).
3. The **averages per subject** are discovered automatically: they are the sensors of the same integration that have
   the `Nom` and `Code` attributes, their state being the average.

When the sensor is first chosen (or changed), the grades already visible are **remembered without any effect** and the
weekly credit is computed from the current averages. Only grades entered afterwards count.

Good to know:

- Subject names are matched ignoring case, accents, punctuation and spaces (`ed.physique & sport.` is sport). A subject
  missing from the table is added automatically (see above).
- In the EcoleDirecte integration, **increase "Maximum notes displayed"** (15 by default): the wallet only sees the
  grades displayed by that sensor.
- If the source is unavailable when a settlement is due (Home Assistant startup, missing sensor), the settlement is
  retried 3 times at 5-minute intervals, then every night; a persistent notification reports the outage and disappears
  once the settlement succeeds.

## Screen time sensors

The wallet can automatically debit the time actually used, from the sensors of the
[`microsoft_family_safety`](https://github.com/noiwid/HAFamilySafety) integration (for example
`sensor.pc_mael_screen_time`). It neither installs nor configures it.

1. Install and configure `microsoft_family_safety`.
2. In the wallet options, *Calculation settings*, choose one or more **screen time sensors**: pick the **device**
   sensor (the PC), not the child's total, which also adds up the other devices.

How it works:

- A sensor's reading is the time used during the day: its `total_seconds` attribute divided by 60, or failing that its
  state in minutes.
- On each new reading, the **difference from the reference reading** is consumed (weekly credit first, then grades
  capital). Fractions of a minute are carried over to the next reading; several sensors add up.
- On a sensor's **first reading** (when chosen in the options), nothing is billed: the usage already elapsed does not
  count.
- The counter resets every night. A **change of day** (`date` attribute) or, failing that, a **decrease** of the
  counter counts as a reset: the new reading is then the consumption since the reset.
- Reference readings are saved with the state: on restart, the difference that occurred during the shutdown is
  consumed, without losing or doubling any minute.
- Automatic consumptions of the same sensor on the same day form **a single journal line**.
- An "unavailable" or "unknown" sensor is ignored.

Limits: the available time follows the sensor's pace (5 minutes by default); usage between the last reading of the
previous day and midnight is not counted; an erroneous numeric reading (an isolated 0) would be counted as new usage
when the real value returns: the journal shows it and the `screen_time_wallet.adjust` service corrects it.

## Blocking when the time runs out

The wallet can switch devices off by itself when the available time is used up. In the options, *Calculation
settings*, choose switches (domain `switch`) in one or both lists; leave them empty to lock by hand.

- **Lock switches**: blocked when **ON**. This is the case of the Family Safety **Account Lock**
  (`switch.<first name>_lock`): ON sets the allowed screen time to 0 on every platform, OFF restores the saved quotas.
- **Allow switches**: blocked when **OFF**.

When the available time is **0 or less**, the wallet puts every chosen switch in its blocked state; when it is positive
again (Monday top-up, new grades, an adjustment), it puts them back in their free state.

- The state is enforced at **each reading** of a screen time sensor, at startup and after a settlement, a consumption or
  an adjustment: switching a lock back by hand while the time is used up is undone at the next reading. To give time,
  use `screen_time_wallet.adjust`.
- Nothing changes while a Monday settlement is due (source unavailable), so a child is never locked on a stale credit.
- A switch that is `unavailable` or `unknown` is skipped and tried again. If a switch call fails, a persistent
  notification names the switch; it is retried at the next reading and the notification disappears on success.
- Delay: the sensor is read every 5 minutes and the Microsoft write takes about a minute, so the block can come several
  minutes after the time runs out (the negative balance is kept in the notes capital). Adding a switch while the time is
  already used up locks immediately. The Family Safety lock is account-wide (Windows, Xbox, mobile).

## Entities

For each child: *Available time*, *Weekly credit*, *Grades capital* (in minutes) and *Last settlement* (date, initial
credit, week credit and the 20 latest movements as attributes).

The *Report* sensor (state: date of the last settlement) keeps every Monday report (the last 52) and exposes, as
Markdown attributes, `last_report`, `history` (the 12 previous reports, newest first) and `forecast`: what the next
Monday settlement will give if nothing changes until then (new weekly credit, grades not counted yet, expected capital
and available time), together with this week's manual movements and reasons. Show it on the child's dashboard with a
Markdown card (replace the entity with yours):

```yaml
type: markdown
title: Report
content: |
  {{ state_attr('sensor.mael_report', 'forecast') }}

  ---
  {{ state_attr('sensor.mael_report', 'last_report') }}
```

Giving or taking time by hand is done with a **script that opens an input window** (minutes and a required reason).
Import the blueprints in one click, then create a script from each one and pick any sensor of the child's wallet:

- Add time (`screen_time_wallet.adjust`): [![Import blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fjocelynlopez%2FHA-screen-time%2Fblob%2Fmain%2Fblueprints%2Fscript%2Fscreen_time_wallet%2Fadd_time.yaml)
- Remove time (`screen_time_wallet.consume`): [![Import blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fjocelynlopez%2FHA-screen-time%2Fblob%2Fmain%2Fblueprints%2Fscript%2Fscreen_time_wallet%2Fremove_time.yaml)

*Settings → Automations & scenes → Blueprints → Import blueprint*, then *Scripts → Add script → Use a blueprint*. When
the script is launched from the dashboard, Home Assistant asks for the minutes and the reason. The reason is shown in the
Monday report (see below). If the import does not work, create a script by hand with the `fields` `minutes` and `reason`
calling the same actions.

> The "Minutes" number entity and the "Add time" / "Remove time" buttons of v0.5.0 were **removed**: the entities that
> remain in the registry are deleted at startup. Remove them from your dashboards if you had added them.

## Services

- `screen_time_wallet.consume`: consumes minutes (`minutes` > 0, optional `reason`), weekly credit first.
- `screen_time_wallet.adjust`: adjusts the grades capital (`minutes` positive or negative, non-zero, optional
  `reason`).

They target a wallet sensor. The entity id depends on Home Assistant's language (in French
`sensor.mael_temps_disponible`, in English `sensor.mael_available_time`), for example:

```yaml
action: screen_time_wallet.consume
target:
  entity_id: sensor.mael_available_time
data:
  minutes: 45
  reason: console game
```

## Development

```bash
uv sync
uv run pytest
```

The project follows [OpenSpec](https://github.com/Fission-AI/OpenSpec): requirements are in `openspec/specs/` and each
test declares the requirement it verifies with the `requirement` marker.

---

# 🇫🇷 Français

[🇬🇧 English](#screen-time-wallet) · 🇫🇷 Français

Intégration personnalisée pour Home Assistant : un **portefeuille de minutes de temps d'écran par enfant**, alimenté
chaque lundi à partir des moyennes et des notes scolaires, et débité automatiquement du temps réellement passé sur
l'ordinateur.

## Fonctionnement

- Chaque lundi à 00h00, un **bilan** verse :
  - un **crédit hebdomadaire** issu de la moyenne générale, remis à sa valeur chaque semaine (non cumulable) ;
  - un **crédit de semaine** issu de la moyenne des notes de la semaine écoulée, ajouté au **capital notes**, qui se
    cumule et peut être négatif.
- Le **temps disponible** est la somme des deux. La consommation débite d'abord le crédit hebdomadaire.
- Un **rapport** explique la semaine à l'enfant chaque lundi (notification persistante, et service `notify` optionnel),
  avec les minutes que chaque note a rapportées :

  ```
  Ton temps de la semaine (lundi 09/11/2026) :
  • Reporté des semaines précédentes : +145 min
  • MATHEMATIQUES 15,2/20 : +138 min
  • FRANCAIS 7/20 : -415 min
  • Complément moyenne générale (15,80) : +227 min
  Temps disponible : 95 min
  ```

  Le *complément moyenne générale* est le crédit hebdomadaire (issu de la moyenne générale) plus la part du crédit de
  notes que les notes de la semaine ne couvrent pas (tout, s'il n'y a aucune note). Les lignes s'additionnent toujours
  au temps disponible. Le rapport liste aussi les **mouvements manuels de la semaine écoulée** (date, minutes signées et raison de chaque
  ajustement ou consommation manuelle, 30 lignes au plus) et le temps consommé automatiquement par chaque capteur, pour pouvoir retracer le solde.

Sans source de notes, le bilan applique le crédit de repli (240 min par défaut). Avec la **source EcoleDirecte**
(voir plus bas), il utilise les vraies moyennes et les vraies notes. Avec les **capteurs de temps d'écran** (voir plus
bas), la consommation est débitée automatiquement.

## Installation

- **HACS** (recommandé) : *Dépôts personnalisés* → ajouter `https://github.com/jocelynlopez/HA-screen-time`
  (catégorie *Intégration*), télécharger, redémarrer Home Assistant.
- **Manuelle** (Home Assistant Container compris) : copier le dossier `custom_components/screen_time_wallet` dans
  `<config>/custom_components/`, puis redémarrer Home Assistant.

Ensuite : *Paramètres → Appareils et services → Ajouter une intégration → Screen Time Wallet* et saisir le prénom de
l'enfant (une entrée par enfant).

## Options

*Configurer* sur l'entrée :

- **Paramètres de calcul** : temps maximal par semaine (heures, pour 20/20 partout), part des notes (%), note pivot,
  poids minimal, nombre minimal de matières, crédit de repli, notes non significatives, rapport hebdomadaire, service de
  notification, capteur de notes EcoleDirecte, capteurs de temps d'écran, interrupteurs de verrouillage et d'autorisation.
- **Matières et multiplicateurs** : ajouter, modifier ou supprimer une matière (nom tel qu'écrit par EcoleDirecte), ou
  cocher **Détecter les matières de la source** pour ajouter d'un coup celles que la source publie. La fenêtre affiche
  la **table courante** (une ligne par matière avec son multiplicateur, par ordre alphabétique) au-dessus du formulaire.

Une note rejetée déclenche une notification.

### Les matières sont détectées automatiquement

À l'activation d'une source et avant chaque bilan, chaque matière publiée par la source (capteurs de moyenne par
matière, avec ou sans moyenne, et matières des notes) qui n'est pas encore dans la table est **ajoutée avec le
multiplicateur 1** et utilisée dans ce calcul. Une notification nomme les matières ajoutées.

- Réglez le multiplicateur d'une matière ajoutée dans *Matières et multiplicateurs* ; **0 l'exclut** du calcul (utile
  pour les rubriques non scolaires, comme la vie de classe). Une matière déjà dans la table, même à 0, n'est jamais
  modifiée.
- Supprimer une matière que la source publie toujours la rajoute avec le multiplicateur 1 à la détection suivante :
  utilisez 0 pour l'exclure.
- **Détecter les matières de la source** (case à cocher de *Matières et multiplicateurs*, le nom de la matière est alors
  facultatif) lance la même détection à la demande et affiche le résultat dans la fenêtre, sans notification. Le
  crédit hebdomadaire n'est pas recalculé : les matières ajoutées comptent à partir du prochain bilan. Le message de
  résultat et la notification des matières ajoutées listent tous deux la table courante.

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
  (`ed.physique & sport.` est le sport). Une matière absente de la table est ajoutée automatiquement (voir plus haut).
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

## Blocage quand le temps est épuisé

Le portefeuille peut bloquer lui-même les appareils quand le temps disponible est épuisé. Dans les options, *Paramètres
de calcul*, choisir des interrupteurs (domaine `switch`) dans l'une ou les deux listes ; les laisser vides pour verrouiller
à la main.

- **Interrupteurs de verrouillage** : bloqué à l'état **ON**. C'est le cas de l'**Account Lock** de Family Safety
  (`switch.<prénom>_lock`) : ON met le temps d'écran autorisé à 0 sur toutes les plateformes, OFF restaure les quotas
  enregistrés.
- **Interrupteurs d'autorisation** : bloqué à l'état **OFF**.

Quand le temps disponible est **inférieur ou égal à 0**, le portefeuille met chaque interrupteur choisi à l'état bloqué ;
quand il redevient positif (recharge du lundi, nouvelles notes, ajustement), il les remet à l'état libre.

- L'état est imposé à **chaque relevé** d'un capteur de temps d'écran, au démarrage et après un bilan, une consommation ou
  un ajustement : un verrou remis à la main alors que le temps est épuisé est annulé au relevé suivant. Pour donner du
  temps, utiliser `screen_time_wallet.adjust`.
- Rien ne change tant qu'un bilan du lundi est dû (source indisponible) : l'enfant n'est jamais bloqué sur un crédit périmé.
- Un interrupteur `unavailable` ou `unknown` est ignoré puis réessayé. Si l'appel d'un interrupteur échoue, une
  notification persistante le nomme ; il est réessayé au relevé suivant et la notification disparaît au succès.
- Délai : le capteur est relevé toutes les 5 minutes et l'écriture Microsoft prend environ une minute, le blocage peut
  donc arriver plusieurs minutes après l'épuisement (le solde négatif est conservé dans le capital notes). Ajouter un
  interrupteur alors que le temps est déjà épuisé verrouille immédiatement. Le verrou Family Safety porte sur tout le
  compte (Windows, Xbox, téléphone).

## Entités

Pour chaque enfant : *Temps disponible*, *Crédit hebdomadaire*, *Capital notes* (en minutes) et *Dernier bilan*
(date, crédit initial, crédit de semaine et 20 derniers mouvements en attributs).

Le capteur *Rapport* (état : date du dernier bilan) conserve tous les rapports du lundi (les 52 derniers) et expose en
attributs Markdown `last_report`, `history` (les 12 rapports précédents, du plus récent au plus ancien) et `forecast` :
ce que donnera le bilan du prochain lundi si rien ne change d'ici là (nouveau crédit hebdomadaire, notes pas encore
comptées, capital et temps disponible attendus), avec les mouvements manuels de la semaine et leurs raisons. Affichez-le
sur le tableau de bord de l'enfant avec une carte Markdown (remplacez l'entité par la vôtre) :

```yaml
type: markdown
title: Rapport
content: |
  {{ state_attr('sensor.mael_rapport', 'forecast') }}

  ---
  {{ state_attr('sensor.mael_rapport', 'last_report') }}
```

Donner ou retirer du temps à la main se fait avec un **script qui ouvre une fenêtre de saisie** (minutes et raison
obligatoire). Importez les blueprints en un clic, puis créez un script depuis chacun en choisissant n'importe quel capteur
du portefeuille de l'enfant :

- Ajouter du temps (`screen_time_wallet.adjust`) : [![Importer le blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fjocelynlopez%2FHA-screen-time%2Fblob%2Fmain%2Fblueprints%2Fscript%2Fscreen_time_wallet%2Fadd_time.yaml)
- Retirer du temps (`screen_time_wallet.consume`) : [![Importer le blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fjocelynlopez%2FHA-screen-time%2Fblob%2Fmain%2Fblueprints%2Fscript%2Fscreen_time_wallet%2Fremove_time.yaml)

*Paramètres → Automatisations et scènes → Blueprints → Importer un blueprint*, puis *Scripts → Ajouter un script →
Utiliser un blueprint*. Quand le script est lancé depuis le tableau de bord, Home Assistant demande les minutes et la
raison. La raison figure dans le rapport du lundi (voir plus bas). Si l'import ne fonctionne pas, créez un script à la
main avec les champs `minutes` et `reason` qui appelle les mêmes actions.

> L'entité numérique « Minutes » et les boutons « Ajouter du temps » / « Retirer du temps » de la v0.5.0 ont été
> **retirés** : les entités restées dans le registre sont supprimées au démarrage. Retirez-les de vos tableaux de bord si
> vous les y aviez ajoutées.

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
