# grade-conversion Specification

## Purpose

Définit comment une note scolaire est préparée avant tout calcul de crédit : normalisation sur 20, poids selon la matière et le coefficient, reconnaissance des notes non numériques et rejet des notes invalides.

## Requirements

### Requirement: Normalisation du barème
Le système SHALL ramener toute note sur 20 avant son utilisation dans un calcul, par `valeur × 20 / barème`. La valeur, le barème et le coefficient peuvent être fournis avec une virgule décimale.

#### Scenario: Note sur 10
- **WHEN** une note de 8/10 est normalisée
- **THEN** elle est traitée comme 16/20

#### Scenario: Note sur 5 avec virgule
- **WHEN** une note « 4,5 » sur « 5 » est normalisée
- **THEN** elle est traitée comme 18/20

#### Scenario: Barème de 15
- **WHEN** une note de 2/15 est normalisée
- **THEN** elle est traitée comme 2,67/20 (2 × 20 / 15)

### Requirement: Multiplicateur par matière
Le système SHALL appliquer à chaque matière, identifiée par son nom d'EcoleDirecte (comparaison insensible à la casse et aux accents), un multiplicateur : MATHEMATIQUES 3, FRANCAIS 3, ANGLAIS LV1 3, ENS.INTEG.SC.&TECHNO 3, HISTOIRE-GEOGRAPHIE 2, EDUCATION MUSICALE 0,5, ARTS PLASTIQUES 0,5, ED PHYSIQUE & SPORT 0,5. Une matière absente de la table SHALL avoir un multiplicateur de 0 et être signalée à l'appelant. La table SHALL être un paramètre de configuration.

#### Scenario: Matière classée
- **WHEN** la matière « HISTOIRE-GEOGRAPHIE » est recherchée dans la table
- **THEN** son multiplicateur est 2

#### Scenario: Matière non classée
- **WHEN** la matière « TECHNOLOGIE », absente de la table, est recherchée
- **THEN** son multiplicateur est 0 et la matière est signalée comme inconnue

#### Scenario: Matière écrite sans accent ou avec une autre casse
- **WHEN** la matière « Francais » ou « français » est recherchée
- **THEN** elle est reconnue comme « FRANCAIS » (multiplicateur 3)

#### Scenario: Table modifiée
- **WHEN** la table est configurée avec « HISTOIRE-GEOGRAPHIE » à 3
- **THEN** son multiplicateur est 3

### Requirement: Rejet des notes invalides
Le système SHALL rejeter et signaler à l'appelant toute note numérique dont le barème est nul ou négatif, dont la valeur est négative ou supérieure au barème, ou dont le coefficient est négatif.

#### Scenario: Valeur supérieure au barème
- **WHEN** une note de 22/20 est fournie
- **THEN** elle est rejetée avec une erreur explicite

#### Scenario: Barème nul
- **WHEN** une note est fournie avec un barème de 0
- **THEN** elle est rejetée avec une erreur explicite

#### Scenario: Coefficient négatif
- **WHEN** une note est fournie avec un coefficient de −1
- **THEN** elle est rejetée avec une erreur explicite

### Requirement: Poids d'une note
Le système SHALL calculer le poids d'une note comme le multiplicateur de sa matière multiplié par son coefficient, ce dernier pouvant être décimal.

#### Scenario: Évaluation principale
- **WHEN** une note de français a un coefficient de 1
- **THEN** son poids est 3

#### Scenario: Évaluation de faible coefficient
- **WHEN** une note d'histoire-géographie a un coefficient de 0,25
- **THEN** son poids est 0,5

#### Scenario: Matière inconnue
- **WHEN** une note appartient à une matière absente de la table
- **THEN** son poids est 0

### Requirement: Note non numérique
Le système SHALL reconnaître comme non notée toute note dont la valeur n'est pas numérique (par exemple « Abs », « Disp », « NE » ou vide). Une telle note ne SHALL entrer dans aucun calcul et ne SHALL produire aucune erreur.

#### Scenario: Élève absent
- **WHEN** la valeur d'une note est « Abs »
- **THEN** la note est reconnue comme non notée et n'est pas rejetée

#### Scenario: Valeur avec virgule
- **WHEN** la valeur d'une note est « 7,5 »
- **THEN** la note est numérique
