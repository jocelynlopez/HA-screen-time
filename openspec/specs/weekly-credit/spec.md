# weekly-credit Specification

## Purpose
Définit comment sont calculés les deux crédits versés chaque lundi : le crédit initial, issu de la moyenne générale, et le crédit de semaine, issu de la moyenne des notes vues pendant la semaine écoulée, avec des taux déduits d'un temps maximal et d'un ratio notes / moyenne.

## Requirements

### Requirement: Paramètres configurables
Le système SHALL exposer comme paramètres de configuration : le temps maximal hebdomadaire (1200 min), la part des notes (0,6), la note pivot (12/20), la table des multiplicateurs de matière, le poids minimal (3), le nombre minimal de matières (4) et le crédit de repli (240 min). Aucune de ces valeurs ne SHALL être figée dans la logique de calcul.

#### Scenario: Valeurs par défaut
- **WHEN** aucun paramètre n'est fourni
- **THEN** le temps maximal est de 1200 min, la part des notes de 0,6, le pivot de 12, le poids minimal de 3, le nombre minimal de matières de 4 et le crédit de repli de 240 min

#### Scenario: Paramètre modifié
- **WHEN** le temps maximal est configuré à 600 min
- **THEN** le crédit initial et le crédit de semaine pour une moyenne de 20/20 valent la moitié de leurs valeurs par défaut

### Requirement: Taux déduits du maximum et du ratio
Le système SHALL calculer le taux de la moyenne par `temps maximal × (1 − part des notes) / ((20 − pivot) × somme des multiplicateurs)` et le taux de la semaine par `temps maximal × part des notes / ((20 − pivot) × somme des multiplicateurs)`. La somme porte sur toutes les matières de la table. Une configuration dont la somme est nulle ou dont le pivot est supérieur ou égal à 20 SHALL être rejetée avec une erreur.

#### Scenario: Taux par défaut
- **WHEN** la table contient les huit matières par défaut (somme des multiplicateurs 15,5)
- **THEN** le taux de la moyenne est d'environ 3,87 min/point et celui de la semaine d'environ 5,81 min/point

#### Scenario: Maximum atteint
- **WHEN** la moyenne générale et la moyenne de la semaine valent 20/20
- **THEN** le crédit initial est de 480 min, le crédit de semaine de 720 min et leur total de 1200 min

#### Scenario: Configuration invalide
- **WHEN** le pivot est configuré à 20
- **THEN** une erreur est signalée

### Requirement: Moyenne générale pondérée
Le système SHALL calculer la moyenne générale comme la moyenne des moyennes par matière pondérée par les multiplicateurs, sur les seules matières qui ont une moyenne fournie et un multiplicateur strictement positif.

#### Scenario: Sept matières avec moyenne
- **WHEN** les moyennes sont anglais 13,85, arts plastiques 17, musique 16, EIST 18, français 10,67, histoire-géographie 17,43 et maths 19,34, sans moyenne en sport
- **THEN** la moyenne générale est d'environ 15,80

#### Scenario: Matière sans moyenne
- **WHEN** le sport n'a pas encore de moyenne
- **THEN** il est ignoré dans la moyenne générale et ne la fait pas baisser

### Requirement: Crédit initial
Le système SHALL calculer le crédit initial par `taux de la moyenne × somme des multiplicateurs × (moyenne générale − pivot)`, arrondi à l'entier de minutes, avec un plancher à 0. Quand moins de matières que le nombre minimal ont une moyenne, le crédit initial SHALL être égal au crédit de repli.

#### Scenario: Moyenne au-dessus du pivot
- **WHEN** la moyenne générale vaut 15,796 sur les sept matières ci-dessus
- **THEN** le crédit initial est de 228 minutes

#### Scenario: Moyenne au pivot ou en dessous
- **WHEN** la moyenne générale vaut 12 ou 10
- **THEN** le crédit initial est de 0 minute

#### Scenario: Repli sous le nombre minimal de matières
- **WHEN** seules trois matières ont une moyenne
- **THEN** le crédit initial est de 240 minutes

#### Scenario: Nombre minimal atteint
- **WHEN** quatre matières ont une moyenne
- **THEN** le crédit initial est calculé par la formule

### Requirement: Moyenne de la semaine
Le système SHALL calculer la moyenne de la semaine comme la moyenne des notes vues pendant la semaine, ramenées sur 20 et pondérées par leur poids. Quand le poids total des notes est inférieur au poids minimal, la différence SHALL être complétée par la moyenne générale, de sorte qu'une semaine sans note ait pour moyenne la moyenne générale.

#### Scenario: Poids suffisant
- **WHEN** les notes de la semaine sont arts plastiques 9/10 de coefficient 0,5 et français 7/20 de coefficient 1, avec une moyenne générale de 15,796
- **THEN** le poids total est de 3,25 et la moyenne de la semaine est d'environ 7,85

#### Scenario: Semaine sans note
- **WHEN** aucune note n'est vue pendant la semaine
- **THEN** la moyenne de la semaine est la moyenne générale

#### Scenario: Note de faible poids
- **WHEN** la seule note est histoire-géographie 4,5/5 de coefficient 0,25 (poids 0,5), avec une moyenne générale de 15,796
- **THEN** la moyenne de la semaine est d'environ 16,16, car le poids manquant est complété par la moyenne générale

### Requirement: Crédit de semaine
Le système SHALL calculer le crédit de semaine par `taux de la semaine × somme des multiplicateurs × (moyenne de la semaine − pivot)`, arrondi à l'entier de minutes, positif ou négatif. Quand le crédit initial est un crédit de repli, le crédit de semaine SHALL valoir 0.

#### Scenario: Semaine sans note
- **WHEN** aucune note n'est vue et la moyenne générale vaut 15,796
- **THEN** le crédit de semaine est de +342 minutes

#### Scenario: Mauvaise semaine
- **WHEN** les notes de la semaine sont arts plastiques 9/10 de coefficient 0,5 et français 7/20 de coefficient 1
- **THEN** le crédit de semaine est de −374 minutes

#### Scenario: Une seule très mauvaise note
- **WHEN** la seule note est français 7/20 de coefficient 1 (poids 3)
- **THEN** le crédit de semaine est de −450 minutes

#### Scenario: Une seule excellente note
- **WHEN** la seule note est maths 20/20 de coefficient 1
- **THEN** le crédit de semaine est de +720 minutes

#### Scenario: Le volume ne gonfle pas le crédit
- **WHEN** les notes de la semaine sont cinq contrôles de maths à 14/20 de coefficient 1
- **THEN** le crédit de semaine est de +180 minutes, inférieur à celui d'un seul 20/20

#### Scenario: Repli
- **WHEN** moins de quatre matières ont une moyenne
- **THEN** le crédit de semaine est de 0 minute

### Requirement: Arrondi des crédits
Le système SHALL arrondir chaque crédit à l'entier de minutes le plus proche, la moitié étant arrondie en s'éloignant de zéro.

#### Scenario: Demi-minute positive
- **WHEN** la table est réduite à une matière de multiplicateur 1, avec un temps maximal de 8 min, une part des notes de 1, un poids minimal de 1, un nombre minimal de matières de 1, une moyenne de 12 dans cette matière et une seule note de 12,5/20 de coefficient 1 dans cette matière
- **THEN** le crédit de semaine exact est de +0,5 et le résultat est +1 minute

#### Scenario: Demi-minute négative
- **WHEN** les mêmes paramètres sont utilisés avec une note de 11,5/20
- **THEN** le crédit de semaine exact est de −0,5 et le résultat est −1 minute

### Requirement: Notes non significatives
Le système SHALL compter les notes non significatives dans la moyenne de la semaine, sauf si l'option d'exclusion est activée, auquel cas elles SHALL en être exclues. L'option SHALL être désactivée par défaut.

#### Scenario: Option désactivée
- **WHEN** une note non significative d'éducation musicale 7/10 de coefficient 1 est vue pendant la semaine
- **THEN** elle entre dans la moyenne de la semaine avec son poids

#### Scenario: Option activée
- **WHEN** l'option d'exclusion est activée et la même note est vue
- **THEN** elle n'entre pas dans la moyenne de la semaine et n'ajoute pas de poids
