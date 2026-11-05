# Design

## Context

Les quatre capteurs du portefeuille (`sensor.py`) partagent un appareil par entrée de configuration (identifiant `(DOMAIN, entry_id)`, nom de l'enfant) et enregistrent les actions `consume` et `adjust` comme services d'entité. Toute modification du temps passe par `WalletRuntime.async_consume` et `async_adjust`, qui enregistrent l'état, notifient les entités et demandent la remise en accord des interrupteurs de blocage. Aucune entité de saisie n'existe. Voir `proposal.md` pour la motivation et la spec `ha-integration` pour le comportement.

## Goals / Non-Goals

**Goals:**
- Pouvoir ajouter ou retirer du temps en deux clics, sans YAML ni cible.
- Que ces commandes aient exactement l'effet des actions existantes (état, journal, blocage).

**Non-Goals:**
- Un bouton de test du blocage, une carte de tableau de bord, un motif de journal libre.

## Decisions

- **Plateformes `number` et `button`** ajoutées à `PLATFORMS`, dans `number.py` et `button.py`. L'appareil est construit par une fonction partagée (nouveau module, utilisée aussi par `sensor.py`) pour que les trois plateformes rejoignent le même appareil et gardent des identifiants uniques `{entry_id}_{clé}`.
- **La valeur des minutes vit dans le runtime** (`control_minutes`, 15 au départ) : l'entité numérique la lit et l'écrit, les boutons la lisent. Elle n'entre pas dans l'état du portefeuille (`Wallet`, stockage) puisque ce n'est pas une donnée de calcul. Elle est restaurée au démarrage par `RestoreNumber` ; sans valeur enregistrée, 15. Alternative écartée : stocker la valeur avec le portefeuille, qui mélangerait un réglage d'interface à l'état comptable.
- **Réglages de l'entité** : minimum 1, maximum 600, pas 5, unité minute, mode champ de saisie ; Home Assistant refuse les valeurs hors limites.
- **Les boutons appellent `runtime.async_adjust` et `runtime.async_consume`** avec la valeur courante et le motif « bouton » (« button » en anglais). Ils héritent donc de l'enregistrement, du journal, des mises à jour de capteurs et du blocage automatique, sans code propre. Pas de regroupement dans le journal : ce sont des gestes manuels (`merge` reste faux).
- **Une erreur de validation** (valeur nulle, par exemple) ne peut pas se produire avec les limites choisies ; si elle survenait, elle serait remontée en `ServiceValidationError` comme pour les actions.

## Risks / Trade-offs

- [Clic accidentel sur « Retirer du temps »] Il retire vraiment du temps et peut bloquer → le journal le montre et « Ajouter du temps » avec la même valeur le compense.
- [Valeur oubliée dans « Minutes »] Une valeur élevée laissée réglée peut être pressée par erreur → 15 par défaut, et la valeur est visible à côté des boutons.
- [Pas de 5 minutes] Impossible d'ajuster d'une seule minute depuis les commandes → l'action `adjust` reste disponible pour les cas fins.

## Hypothèses à confirmer

Points que la demande n'a pas tranchés et que les specs écrivent. À valider ou corriger avant l'implémentation :
- Valeur des minutes de 1 à 600, par pas de 5, 15 par défaut, restaurée au redémarrage.
- « Ajouter du temps » ajuste le capital notes (comme `adjust`), « Retirer du temps » consomme (comme `consume`).
- Le motif du journal est « bouton » en français et « button » en anglais.
- Pas de regroupement des gestes manuels dans le journal.
- Pas de bouton de test du blocage.
