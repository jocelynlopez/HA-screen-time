# Design

## Context

Le portefeuille sait déjà consommer des minutes (`Wallet.consume`, service `consume`) : crédit hebdomadaire d'abord, puis capital notes, avec un journal. Il manque la source de la consommation. L'intégration `microsoft_family_safety` (HACS, `noiwid/HAFamilySafety`) publie, selon son README, `sensor.{appareil}_screen_time` (minutes utilisées *aujourd'hui* sur un appareil) et `sensor.{préfixe}_screen_time` (total par enfant), rafraîchis toutes les 300 s par défaut. Observé sur `sensor.pc_mael_screen_time` : unité `min`, attributs `total_seconds` (660 pour 11 minutes), `date` (jour du relevé), `hours`, `minutes` et `seconds` ; le compteur repart de 0 à minuit (à 5 minutes près) en même temps que `date` change, sans passer par « unavailable ». Voir `proposal.md` pour la motivation et les specs `screen-time-usage`, `screen-time-wallet` et `ha-integration` pour le comportement.

## Goals / Non-Goals

**Goals:**
- Débiter le portefeuille de l'usage réel, sans perdre ni doubler de minute à travers redémarrages, rechargements et remises à zéro.
- Une logique de calcul pure et testable, indépendante de l'heure de remise à zéro.

**Non-Goals:**
- Verrouiller le PC, mesurer le téléphone, installer ou configurer l'intégration Family Safety.

## Decisions

- **Calcul pur dans le cœur** (`engine/usage.py`, `consumed_since(référence, minutes, jour)`) : renvoie les minutes entières consommées et la nouvelle référence (valeur et jour). Un changement de jour, ou à défaut de jour une baisse du compteur, vaut remise à zéro (référence 0). Le jour est l'attribut `date` observé ; il couvre le cas où la valeur monte malgré la remise à zéro (190 la veille, 200 au redémarrage du lendemain). La baisse reste le repli sans attribut. Une référence sans jour ne déclenche pas de remise à zéro par le jour : seule la valeur est comparée, puis le jour est mémorisé. Le jour est comparé par égalité, pas par ordre.
- **Relevé en secondes** : le relevé est `total_seconds` / 60 quand l'attribut est numérique, sinon l'état en minutes. L'attribut `minutes` n'est pas utilisé : il pourrait n'être que la composante minutes de `hours`/`minutes`/`seconds`. La lecture se fait dans la couche Home Assistant, le cœur ne reçoit que des minutes.
- **Référence qui n'avance que des minutes consommées** : un relevé fractionnaire ne perd rien (10 → 10,6 ne consomme pas, la référence reste 10 ; 11,2 consomme 1). Alternative écartée : arrondir chaque relevé, qui fausserait le total sur la durée.
- **Écoute des changements d'état** (`async_track_state_change_event`) plutôt qu'un sondage : le débit suit le rythme du capteur (5 minutes par défaut). Toute lecture passe par le verrou de l'objet d'exécution, avec le bilan et les services.
- **Références enregistrées avec l'état** (clé `usage_baselines` : `{entité: {"minutes": "n/d", "date": "2026-11-04" | null}}`, fractions notées `n/d`, à côté de `source_entity`, ignorées par `Wallet.from_dict`). Au chargement, on relève chaque capteur et on consomme la différence ; les références des capteurs retirés des options sont supprimées.
- **Au démarrage, bilan avant consommation** : si un lundi a été manqué, le crédit hebdomadaire est d'abord remplacé, puis l'usage accumulé pendant l'arrêt est débité du nouveau crédit. Une minute utilisée avant le lundi peut ainsi être imputée à la semaine suivante, imprécision acceptée pour ce cas rare.
- **Regroupement dans le journal** : `Wallet.consume(..., merge=True)` ajoute au dernier mouvement de consommation de même motif et de même jour. Sans cela, un relevé toutes les 5 minutes remplirait les 200 mouvements du journal en quelques jours et en chasserait les bilans.
- **Option** : sélecteur d'entités multiple limité aux capteurs, sans filtre sur l'intégration (les forks de Family Safety n'ont pas le même domaine). Un champ vidé est lu comme « aucun capteur ».
- **Motif** : nom convivial du capteur, repli sur son identifiant.

## Risks / Trade-offs

- [Relevé transitoirement à 0 ou erroné] Si le capteur passe un instant à 0 sans raison puis revient à sa vraie valeur, le retour est compté comme une nouvelle consommation (190 minutes par exemple) → les relevés « indisponible » ou « inconnu » sont ignorés, ce qui couvre le cas courant ; un 0 numérique erroné reste possible, visible dans le journal et corrigeable avec le service d'ajustement.
- [Comportement de Family Safety] Observé : remise à zéro à minuit avec changement de `date`, sans « unavailable ». Non vérifié : le comportement au-delà de 60 minutes d'usage et en cas de coupure du rafraîchissement → la lecture par `total_seconds` évite la confusion possible avec la composante `minutes`, et le premier suivi réel reste à faire.
- [Retard de relevé] Le débit suit le capteur (5 minutes par défaut) : le temps disponible peut avoir jusqu'à 5 minutes de retard, et l'usage entre le dernier relevé de la veille et minuit n'est pas compté (5 minutes au plus), imprécision acceptée.
- [Premier relevé en cours de journée] L'usage déjà écoulé n'est pas facturé → voulu, pour qu'un branchement en milieu de journée ne pénalise pas.

## Hypothèses à confirmer

Points que la demande n'a pas tranchés et que les specs écrivent. À valider ou corriger avant l'implémentation :
- Le relevé est `total_seconds` / 60, avec l'état en repli ; un changement d'attribut `date` ou, sans date, une baisse signifie une remise à zéro.
- Au premier relevé d'un capteur, rien n'est facturé.
- Les consommations automatiques d'un même capteur sont regroupées par jour dans le journal.
- L'option accepte n'importe quel capteur (pas seulement ceux de `microsoft_family_safety`).
- Au démarrage, le bilan du lundi est fait avant la consommation accumulée pendant l'arrêt.
- Un saut important du compteur est accepté tel quel (pas de plafond par relevé).
- Le motif du journal est le nom convivial du capteur.
