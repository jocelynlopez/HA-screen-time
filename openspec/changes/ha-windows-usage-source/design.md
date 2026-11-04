# Design

## Context

Le portefeuille sait déjà consommer des minutes (`Wallet.consume`, service `consume`) : crédit hebdomadaire d'abord, puis capital notes, avec un journal. Il manque la source de la consommation. L'intégration `microsoft_family_safety` (HACS, `noiwid/HAFamilySafety`) publie, selon son README, `sensor.{appareil}_screen_time` (minutes utilisées *aujourd'hui* sur un appareil) et `sensor.{préfixe}_screen_time` (total par enfant), rafraîchis toutes les 300 s par défaut. Son README ne dit pas quand le compteur repart de zéro. Voir `proposal.md` pour la motivation et les specs `screen-time-usage`, `screen-time-wallet` et `ha-integration` pour le comportement.

## Goals / Non-Goals

**Goals:**
- Débiter le portefeuille de l'usage réel, sans perdre ni doubler de minute à travers redémarrages, rechargements et remises à zéro.
- Une logique de calcul pure et testable, indépendante de l'heure de remise à zéro.

**Non-Goals:**
- Verrouiller le PC, mesurer le téléphone, installer ou configurer l'intégration Family Safety.

## Decisions

- **Calcul pur dans le cœur** (`engine/usage.py`, `consumed_since(référence, relevé)`) : renvoie les minutes entières consommées et la nouvelle référence. Une baisse du compteur vaut remise à zéro (référence 0), ce qui évite de deviner l'heure de remise à zéro, inconnue. Alternative écartée : lire l'attribut `date` ou supposer minuit, deux hypothèses invérifiables ici.
- **Référence qui n'avance que des minutes consommées** : un relevé fractionnaire ne perd rien (10 → 10,6 ne consomme pas, la référence reste 10 ; 11,2 consomme 1). Alternative écartée : arrondir chaque relevé, qui fausserait le total sur la durée.
- **Écoute des changements d'état** (`async_track_state_change_event`) plutôt qu'un sondage : le débit suit le rythme du capteur (5 minutes par défaut). Toute lecture passe par le verrou de l'objet d'exécution, avec le bilan et les services.
- **Références enregistrées avec l'état** (clé `usage_baselines`, fractions notées `n/d`, à côté de `source_entity`, ignorées par `Wallet.from_dict`). Au chargement, on relève chaque capteur et on consomme la différence ; les références des capteurs retirés des options sont supprimées.
- **Au démarrage, bilan avant consommation** : si un lundi a été manqué, le crédit hebdomadaire est d'abord remplacé, puis l'usage accumulé pendant l'arrêt est débité du nouveau crédit. Une minute utilisée avant le lundi peut ainsi être imputée à la semaine suivante, imprécision acceptée pour ce cas rare.
- **Regroupement dans le journal** : `Wallet.consume(..., merge=True)` ajoute au dernier mouvement de consommation de même motif et de même jour. Sans cela, un relevé toutes les 5 minutes remplirait les 200 mouvements du journal en quelques jours et en chasserait les bilans.
- **Option** : sélecteur d'entités multiple limité aux capteurs, sans filtre sur l'intégration (les forks de Family Safety n'ont pas le même domaine). Un champ vidé est lu comme « aucun capteur ».
- **Motif** : nom convivial du capteur, repli sur son identifiant.

## Risks / Trade-offs

- [Relevé transitoirement à 0 ou erroné] Si le capteur passe un instant à 0 sans raison puis revient à sa vraie valeur, le retour est compté comme une nouvelle consommation (190 minutes par exemple) → les relevés « indisponible » ou « inconnu » sont ignorés, ce qui couvre le cas courant ; un 0 numérique erroné reste possible, visible dans le journal et corrigeable avec le service d'ajustement.
- [Comportement de Family Safety non observé] L'heure de remise à zéro, la précision en minutes et l'attribution Windows / autres plateformes n'ont pas été vérifiées → le calcul ne dépend d'aucune de ces hypothèses, mais le premier test réel reste à faire.
- [Retard de relevé] Le débit suit le capteur (5 minutes par défaut) : le temps disponible peut avoir jusqu'à 5 minutes de retard.
- [Premier relevé en cours de journée] L'usage déjà écoulé n'est pas facturé → voulu, pour qu'un branchement en milieu de journée ne pénalise pas.

## Hypothèses à confirmer

Points que la demande n'a pas tranchés et que les specs écrivent. À valider ou corriger avant l'implémentation :
- L'état du capteur est le nombre de minutes utilisées aujourd'hui ; une baisse signifie une remise à zéro.
- Au premier relevé d'un capteur, rien n'est facturé.
- Les consommations automatiques d'un même capteur sont regroupées par jour dans le journal.
- L'option accepte n'importe quel capteur (pas seulement ceux de `microsoft_family_safety`).
- Au démarrage, le bilan du lundi est fait avant la consommation accumulée pendant l'arrêt.
- Un saut important du compteur est accepté tel quel (pas de plafond par relevé).
- Le motif du journal est le nom convivial du capteur.
