# Design

## Context

`Wallet.activate_source(now, averages, notes)` ajoute à `seen_keys` la clé de toutes les notes visibles. `Wallet.settle` ne compte que les notes dont la clé n'y figure pas. Une clé (`Grade.key`) est un tuple (date, matière, commentaire, barème, coefficient) ; `Grade.date` est une date ou un texte AAAA-MM-JJ. Les actions `consume` et `adjust` sont des actions d'entité enregistrées sur la plateforme `sensor`. Voir `proposal.md`.

## Goals / Non-Goals

**Goals:**
- Ne plus perdre les notes de la semaine en cours à l'activation.
- Pouvoir corriger un portefeuille déjà activé sans toucher aux crédits.

**Non-Goals:**
- Migrer automatiquement les portefeuilles existants, recompter d'anciennes semaines.

## Decisions

- **Date de la note** : on utilise le champ `date` de la note (jour de l'évaluation), pas la date de saisie. Une date illisible est traitée comme ancienne (la note est mémorisée sans effet), par prudence.
- **Début de semaine** : `monday_midnight(now)`, comme pour les bilans. Une note est « de la semaine en cours » si sa date est postérieure ou égale à ce lundi.
- **Activation** : `activate_source` ne mémorise que les notes antérieures à ce lundi ; les autres restent absentes de `seen_keys` et seront comptées par le prochain bilan. Le reste de l'activation est inchangé (crédit initial, journal).
- **Recomptage** : `Wallet.recount_week(now, notes)` retire de `seen_keys` les clés des notes datées du lundi en cours ou après, et renvoie leur nombre. Il ne modifie ni les crédits ni le journal : ce n'est pas un mouvement de temps.
- **Action** : `WalletRuntime.async_recount_week` relit la source (les clés vues sont des clés, pas des notes), applique le recomptage sous le verrou du runtime, enregistre l'état et rafraîchit la prévision. Si la source est inaccessible, l'action lève `ServiceValidationError` et rien ne change. Elle est enregistrée sur la plateforme `sensor` avec un schéma vide, comme `consume` et `adjust`.
- **Pas de journal** : aucune ligne n'est ajoutée au journal, qui ne contient que des mouvements de temps.

## Risks / Trade-offs

- [Double comptage après un bilan tardif] Si un bilan a été rattrapé en retard (source indisponible le lundi) et a compté des notes datées de la semaine en cours, l'action les rend à compter une seconde fois → à utiliser pour corriger une activation faite en cours de semaine, ce que le README précise. Détecter ce cas demanderait d'enregistrer les notes comptées par chaque bilan, ce qui change l'état et dépasse ce change.
- [Date de la note ≠ date de saisie] Une note datée d'une semaine précédente mais saisie cette semaine reste mémorisée → elle compte pour la semaine où elle a été donnée, pas pour celle où elle a été saisie ; cohérent avec la règle actuelle.
- [Activation en début de semaine] Activer un lundi à 00h00 ou le mardi compte tout ce qui est daté depuis ce lundi → c'est voulu : ces notes appartiennent à la semaine qui va être soldée.

## Hypothèses à confirmer

Points que la demande n'a pas tranchés et que les specs écrivent. À valider ou corriger avant l'implémentation :
- La date de la note est celle du champ `date`, pas la date de saisie.
- Seules les notes de la semaine en cours sont concernées (activation et recomptage) ; celles d'avant le lundi ne sont jamais rendues à compter.
- L'action est une action d'entité comme `consume`, sans mouvement au journal, avec un schéma vide.
- Une note de la semaine en cours déjà comptée par un bilan tardif peut être recomptée par erreur : le risque est accepté et documenté dans le README.
- Aucune migration automatique des portefeuilles déjà activés : le parent lance l'action une fois.
- Version mineure `0.9.0`.
