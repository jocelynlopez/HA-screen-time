# Proposal

## Why

Le modèle livré (allocation fixe de 240 min par semaine, plus un effet direct de chaque note) a deux défauts constatés sur les vraies données d'EcoleDirecte : une semaine sans note (vacances) laisse l'élève en retard sur une semaine ordinaire, et le nombre de notes pèse autant que leur qualité (cinq 14/20 rapportent plus qu'un 20/20). Le modèle est donc remplacé par un bilan hebdomadaire du lundi qui s'appuie sur les moyennes, avec un temps hebdomadaire non cumulable et un capital issu des notes, durable. Cette étape ne touche que la logique métier en Python, sans Home Assistant ni connexion à EcoleDirecte.

## What Changes

- Deux compartiments dans le portefeuille :
  - un **crédit hebdomadaire**, remis à sa valeur chaque lundi et perdu s'il n'est pas utilisé ;
  - un **capital notes**, cumulé d'une semaine à l'autre, qui peut être négatif.
  Le temps disponible est leur somme.
- Un **bilan chaque lundi à 00h00** :
  - le crédit hebdomadaire est remplacé par le **crédit initial**, calculé à partir de la moyenne générale pondérée ;
  - le capital notes reçoit le **crédit de semaine**, calculé à partir de la moyenne pondérée des notes vues pendant la semaine écoulée (complétée par la moyenne générale quand le poids des notes est inférieur à un poids minimal, donc égale à la moyenne générale sans note).
- Les deux crédits suivent `taux × somme des multiplicateurs × (moyenne − pivot)`. Les taux se déduisent d'un **temps maximal hebdomadaire** (20 h pour 20/20 partout) et d'un **ratio notes / moyenne** (60 % / 40 %) : ils ne sont plus des constantes.
- Règle de démarrage : moins de 4 matières avec une moyenne → crédit initial de repli (240 min) et pas de crédit de semaine.
- Le poids d'une note est multiplicateur de matière × coefficient. Les noms de matières sont ceux d'EcoleDirecte. Une matière inconnue est sans effet et signalée à l'appelant.
- Une note n'est jamais comptée deux fois (clé date + matière + commentaire + barème + coefficient, sans la valeur) ; l'historique déjà visible à la création est mémorisé sans effet.
- La consommation débite d'abord le crédit hebdomadaire, puis le capital notes.
- **BREAKING** : l'effet direct de chaque note, le taux de 15 min/point, l'allocation fixe de 240 min et le report de tout le solde disparaissent.

## Capabilities

### New Capabilities
- `weekly-credit`: calcul du crédit initial (moyenne générale) et du crédit de semaine (moyenne des notes de la semaine), taux déduits du temps maximal et du ratio, repli sous 4 matières, poids minimal, arrondi.

### Modified Capabilities
- `grade-conversion`: la conversion d'une note en minutes disparaît ; la capability ne porte plus que la normalisation sur 20, le poids d'une note, la table des multiplicateurs (noms d'EcoleDirecte, matière inconnue signalée) et la validation des notes.
- `screen-time-wallet`: le solde unique, l'allocation fixe, le report intégral et l'effet direct des notes sont remplacés par les deux compartiments, le bilan du lundi, les notes de la semaine et la consommation.

## Impact

- `src/portefeuille_minutes/` : `config.py` (nouveaux paramètres), `grades.py` (plus de conversion en minutes), nouveau module de calcul des crédits, `wallet.py` réécrit.
- `tests/` : tous les tests des deux specs sont réécrits ; le test de couverture des exigences lit aussi les deltas des changes en cours.
- Aucune dépendance ajoutée, aucun accès réseau.

## Hors périmètre

- Intégration Home Assistant (capteurs, options, notifications, persistance) et lecture des capteurs EcoleDirecte.
- Calcul des moyennes par matière : elles sont fournies en entrée (capteurs EcoleDirecte, qui excluent déjà les notes non significatives).
- Mesure de la consommation (Windows, prise connectée, Family Link) et ajustement manuel parental.
- Plafond du capital notes : aucun dans ce change.
