# Proposal

## Why

Le rapport du lundi et la prévision détaillent le calcul (crédit initial, moyennes, poids, pivot) mais ne disent pas ce que chaque note a rapporté en minutes. Pour l'enfant, c'est difficile à lire : il veut voir « Maths 15,2 → +138 min » et comprendre d'où vient son temps disponible, sans formule.

## What Changes

- **Minutes par note** : le compte rendu du bilan donne, pour chaque note comptée, les minutes signées qu'elle apporte au crédit de semaine (positives au-dessus de la note pivot, négatives en dessous).
- **Temps reporté et complément** : le compte rendu donne aussi le capital reporté des semaines précédentes et un « complément moyenne générale » (crédit hebdomadaire issu de la moyenne générale, plus la part du crédit de notes que les notes de la semaine ne couvrent pas). La somme du reporté, des minutes des notes et du complément est exactement le temps disponible.
- **Rapport simplifié pour l'enfant** : le rapport du lundi, la prévision et l'historique affichent un bloc « Ton temps de la semaine (lundi JJ/MM) » : reporté des semaines précédentes (s'il est non nul), une ligne par note, « Complément moyenne générale (moyenne) », « Temps disponible ». Le détail technique actuel (crédit initial, moyenne de la semaine, poids, crédit de semaine, capital) est supprimé du rapport. La semaine de repli garde son affichage actuel.
- **README** : exemple de rapport, anglais et français.

## Capabilities

### New Capabilities
Aucune.

### Modified Capabilities
- `screen-time-wallet`: minutes apportées par chaque note, capital reporté et complément dans le compte rendu.
- `ha-integration`: nouveau contenu du rapport hebdomadaire.

## Impact

- `engine/credit.py` (minutes par note dans `WeekDetails`), `engine/wallet.py` (`Report` : minutes par note, reporté, complément), `report.py` et traductions (nouveau bloc, anciens textes du détail supprimés), tests existants du contenu du rapport, `README.md`.
- Le calcul des crédits et l'état enregistré ne changent pas. Les rapports déjà enregistrés gardent leur ancien texte. Version mineure `0.8.0`.

## Hors périmètre

- Modifier la règle de calcul (une semaine sans note rapporte toujours +321 min de crédit de notes si la moyenne générale dépasse le pivot).
- Réécrire les rapports déjà enregistrés dans l'historique.
- Afficher le détail technique ailleurs (par exemple en option).
