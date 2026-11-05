# Design

## Context

`credit.week_details` calcule le crédit de semaine : `taux_semaine × somme des multiplicateurs × (moyenne de la semaine − pivot)`, avec `moyenne de la semaine = (Σ poids_i × note_i + max(0, poids minimal − poids total) × moyenne générale) ÷ max(poids total, poids minimal)`. `Wallet.settle` fabrique un `Report` par lundi, et `report.py` le met en forme (`render_report`, `render_forecast` via `_report_lines`). Voir `proposal.md`.

## Goals / Non-Goals

**Goals:**
- Montrer ce que chaque note a rapporté, en minutes, et d'où vient le temps disponible, dans un bloc lisible par un enfant.

**Non-Goals:**
- Changer la règle de calcul, réécrire l'historique des rapports.

## Decisions

- **Apport linéaire d'une note** : le crédit de semaine est linéaire en chaque note. Avec `k = taux_semaine × somme des multiplicateurs` et `D = max(poids total, poids minimal)`, une note apporte `k × poids × (note sur 20 − pivot) ÷ D`. La somme des apports plus la part de la moyenne générale (`k × max(0, poids minimal − poids total) × (moyenne générale − pivot) ÷ D`) vaut exactement le crédit de semaine non arrondi. `week_details` calcule les apports des notes comptées (celles que la moyenne retient réellement, donc sans les notes non significatives quand l'option les ignore) et les arrondit à l'entier le plus proche, demi vers l'écart à zéro, comme les crédits.
- **Complément = reste** : au lieu de l'arrondir lui aussi, le complément vaut `crédit initial + crédit de semaine − somme des minutes arrondies des notes`. Ainsi `reporté + minutes des notes + complément = temps disponible` exactement, sans écart d'arrondi à expliquer à l'enfant. Il contient le crédit hebdomadaire (les 40 %) et la part des 60 % que les notes ne couvrent pas (tout le crédit de semaine s'il n'y a aucune note).
- **Reporté** : `Wallet.settle` note le capital notes avant d'y ajouter le crédit de semaine ; le `Report` le porte (`carried`). Pour des lundis rattrapés, chaque rapport porte le capital de son propre lundi.
- **Report** : trois champs ajoutés, `note_minutes` (liste de notes avec leurs minutes), `carried` et `complement`. `counted`, `rejected` et le reste restent pour les anomalies.
- **Rendu** : `_report_lines` produit le bloc de l'enfant ; `render_report` le précède de « Ton temps de la semaine (lundi JJ/MM) : », `render_forecast` du titre de prévision. Les textes du détail technique (crédit initial, notes de la semaine avec poids, moyenne de la semaine, crédit de semaine, capital) disparaissent. La moyenne générale reste visible entre parenthèses dans la ligne du complément. Les sections de mouvements manuels et de consommation automatique sont inchangées.
- **Semaine de repli** : pas de minutes par note ni de complément ; les lignes de repli actuelles (crédit initial de repli, crédit de semaine 0, capital et temps disponible) sont conservées.
- **Aucune migration** : l'état enregistré ne change. Les rapports de l'historique sont du texte déjà rendu : ils gardent leur ancien affichage.

## Risks / Trade-offs

- [Perte du détail technique] Le parent ne voit plus le poids ni la moyenne de la semaine dans le rapport → décision assumée ; les valeurs restent dans les options et le journal du capteur « Dernier bilan ».
- [Note ajoutée à un complément partiel] Quand le poids des notes est inférieur au minimum, chaque nouvelle note fait baisser la part du complément → c'est la règle de calcul actuelle, visible dans la prévision.
- [Rapports de transition] L'historique mélange anciens et nouveaux formats → un seul rapport concerné par version.

## Hypothèses à confirmer

Points que la demande n'a pas tranchés et que les specs écrivent. À valider ou corriger avant l'implémentation :
- Le libellé du capital reporté est « Reporté des semaines précédentes » (et non « Temps non consommé »), car le capital cumule plusieurs semaines et le crédit hebdomadaire non consommé est perdu le lundi ; la ligne n'apparaît que si le capital est non nul, avec un signe moins s'il est négatif.
- Le détail technique du calcul est supprimé du rapport (la moyenne générale reste entre parenthèses dans le complément).
- Une ligne par note comptée avec ses minutes signées ; les notes écartées ou non significatives ignorées n'ont pas de ligne.
- Le complément est le reste qui rend la somme exacte (reporté + notes + complément = temps disponible), pas un arrondi indépendant.
- Le rapport du lundi, la prévision et les rapports futurs de l'historique adoptent ce rendu ; la semaine de repli garde son affichage ; les anciens rapports enregistrés ne changent pas.
- Version mineure `0.8.0`.
