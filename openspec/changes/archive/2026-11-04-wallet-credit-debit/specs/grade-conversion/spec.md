# Spec Delta

## Purpose

Définit comment une note scolaire est convertie en un nombre de minutes de temps d'écran à créditer (note au-dessus du pivot) ou à débiter (note en dessous), selon la matière, le coefficient et le barème.

## ADDED Requirements

### Requirement: Formule de conversion
Le système SHALL calculer les minutes d'une note par `taux de base × multiplicateur de la matière × (note sur 20 − note pivot) × coefficient`. Un résultat positif est un crédit, un résultat négatif est un débit.

#### Scenario: Note au-dessus du pivot
- **WHEN** une note de 15/20 en maths (multiplicateur 3) de coefficient 1 est convertie, avec un taux de base de 15 min/point et un pivot de 12
- **THEN** le résultat est +135 minutes

#### Scenario: Note en dessous du pivot
- **WHEN** une note de 8/20 en français (multiplicateur 4) de coefficient 1 est convertie, avec les mêmes paramètres
- **THEN** le résultat est −240 minutes

#### Scenario: Note égale au pivot
- **WHEN** une note de 12/20 est convertie
- **THEN** le résultat est 0 minute

### Requirement: Note pivot
Le système SHALL comparer la note, ramenée sur 20, à une note pivot de 12/20 par défaut. Le pivot SHALL être un paramètre de configuration.

#### Scenario: Pivot modifié
- **WHEN** le pivot est configuré à 10 et une note de 15/20 en maths de coefficient 1 est convertie
- **THEN** le résultat est +225 minutes

### Requirement: Normalisation du barème
Le système SHALL ramener toute note sur 20 avant la conversion, par `valeur × 20 / barème`.

#### Scenario: Note sur 10
- **WHEN** une note de 8/10 en maths de coefficient 1 est convertie
- **THEN** elle est traitée comme 16/20 et le résultat est +180 minutes

### Requirement: Multiplicateur par matière
Le système SHALL appliquer un multiplicateur propre à la matière : maths 3, français 4, histoire 2, anglais 3, EIST 3, musique 0,5, arts plastiques 0,5, sport 0,5. Une matière absente de cette table SHALL avoir un multiplicateur de 0, donc aucun effet sur le solde. La table SHALL être un paramètre de configuration.

#### Scenario: Matière classée
- **WHEN** une note de 14/20 en histoire de coefficient 1 est convertie
- **THEN** le résultat est +60 minutes

#### Scenario: Matière non classée
- **WHEN** une note de 5/20 en technologie, absente de la table, est convertie
- **THEN** le résultat est 0 minute

#### Scenario: Matière écrite sans accent ou avec une autre casse
- **WHEN** une note est fournie avec la matière « Francais » ou « français »
- **THEN** elle est reconnue comme la matière « français »

### Requirement: Taux de base
Le système SHALL utiliser un taux de base de 15 minutes par point d'écart, paramétrable sans modifier la logique de calcul.

#### Scenario: Taux de base modifié
- **WHEN** le taux de base est configuré à 10 et une note de 15/20 en maths de coefficient 1 est convertie
- **THEN** le résultat est +90 minutes

### Requirement: Coefficient
Le système SHALL multiplier le montant par le coefficient de l'évaluation, qui peut être décimal.

#### Scenario: Évaluation à fort coefficient
- **WHEN** une note de 15/20 en maths de coefficient 3 est convertie
- **THEN** le résultat est +405 minutes

#### Scenario: Coefficient décimal
- **WHEN** une note de 15/20 en maths de coefficient 0,5 est convertie
- **THEN** le résultat est arrondi à +68 minutes (67,5 arrondi)

### Requirement: Arrondi
Le système SHALL arrondir le résultat à l'entier de minutes le plus proche, la moitié étant arrondie en s'éloignant de zéro.

#### Scenario: Demi-minute positive
- **WHEN** une note de 13/20 en sport de coefficient 1 est convertie (résultat exact +7,5)
- **THEN** le résultat est +8 minutes

#### Scenario: Demi-minute négative
- **WHEN** une note de 11/20 en sport de coefficient 1 est convertie (résultat exact −7,5)
- **THEN** le résultat est −8 minutes

### Requirement: Rejet des notes invalides
Le système SHALL rejeter avec une erreur explicite toute note dont le barème est nul ou négatif, dont la valeur est négative ou supérieure au barème, ou dont le coefficient est négatif.

#### Scenario: Valeur supérieure au barème
- **WHEN** une note de 22/20 est fournie
- **THEN** une erreur est signalée et aucune minute n'est calculée

#### Scenario: Barème nul
- **WHEN** une note est fournie avec un barème de 0
- **THEN** une erreur est signalée
