# Spec Delta

## Purpose

Définit comment le portefeuille lit les notes et les moyennes par matière publiées dans Home Assistant par l'intégration EcoleDirecte, et les traduit en données de bilan, sans jamais se connecter lui-même à EcoleDirecte.

## ADDED Requirements

### Requirement: Lecture des notes
Le système SHALL lire les notes dans l'attribut `notes` du capteur de notes choisi et les traduire en notes du portefeuille, avec la date, la matière, le commentaire, la valeur, le barème, le coefficient et l'indicateur non significatif. Les valeurs textuelles avec virgule décimale SHALL être acceptées. Une entrée sans date ou sans matière SHALL être ignorée.

#### Scenario: Note complète
- **WHEN** une entrée a pour date « 2026-11-02 », matière « FRANCAIS », commentaire « Evaluation sommative séquence I », note « 7 », sur « 20 », coefficient « 1 » et non significatif faux
- **THEN** elle devient une note de français de 7/20, de coefficient 1, comptée normalement

#### Scenario: Virgule décimale
- **WHEN** une entrée a pour note « 4,5 », sur « 5 » et coefficient « 0,25 »
- **THEN** la note vaut 4,5/5 avec un coefficient de 0,25

#### Scenario: Note non significative
- **WHEN** une entrée a l'indicateur non significatif à vrai
- **THEN** la note est marquée non significative

#### Scenario: Valeur non numérique
- **WHEN** une entrée a pour note « Abs »
- **THEN** elle est transmise telle quelle comme note non numérique

#### Scenario: Entrée incomplète
- **WHEN** une entrée n'a pas de matière
- **THEN** elle est ignorée sans erreur

#### Scenario: Aucune note
- **WHEN** l'attribut `notes` est une liste vide
- **THEN** la source fournit zéro note

### Requirement: Découverte des moyennes par matière
Le système SHALL découvrir les capteurs de moyenne parmi les entités rattachées à la même entrée de configuration EcoleDirecte que le capteur de notes, en retenant celles qui ont les attributs `Nom` et `Code`. Le nom de la matière SHALL être l'attribut `Nom` et la moyenne l'état du capteur. Les capteurs d'une autre entrée EcoleDirecte et ceux sans ces attributs SHALL être ignorés.

#### Scenario: Sept moyennes
- **GIVEN** huit capteurs de matière, dont celui du sport sans donnée
- **WHEN** les moyennes sont lues
- **THEN** la source fournit les sept moyennes disponibles, par nom de matière

#### Scenario: Capteurs étrangers ignorés
- **WHEN** le capteur de notes lui-même, ou un capteur d'une autre entrée EcoleDirecte (un autre enfant), existe
- **THEN** il n'est pas pris comme capteur de moyenne

#### Scenario: Nom de matière du sport
- **WHEN** le capteur de sport a pour attribut `Nom` « ed.physique & sport. »
- **THEN** sa moyenne est rattachée à la matière « ED PHYSIQUE & SPORT » de la table des multiplicateurs

### Requirement: Moyenne indisponible
Le système SHALL ignorer sans erreur un capteur de matière dont l'état est inconnu, indisponible, vide ou non numérique.

#### Scenario: Sport sans moyenne
- **WHEN** l'état du capteur de sport est « unknown »
- **THEN** le sport n'apparaît pas dans les moyennes et aucune erreur n'est signalée

### Requirement: Capteur de notes indisponible
Le système SHALL signaler une erreur de source quand le capteur de notes n'existe pas, est indisponible ou inconnu, ou n'a pas d'attribut `notes`, de sorte que le bilan soit reporté.

#### Scenario: Capteur indisponible
- **WHEN** l'état du capteur de notes est « unavailable »
- **THEN** la source signale une erreur

#### Scenario: Capteur absent
- **WHEN** l'entité configurée n'existe plus
- **THEN** la source signale une erreur

#### Scenario: Aucune moyenne découverte
- **WHEN** le capteur de notes est disponible mais qu'aucun capteur de matière n'est trouvé
- **THEN** la source fournit les notes et un ensemble de moyennes vide, ce qui conduit au crédit de repli
