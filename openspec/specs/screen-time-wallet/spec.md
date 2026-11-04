# screen-time-wallet Specification

## Purpose

Définit le portefeuille de minutes de temps d'écran : son solde, l'allocation hebdomadaire de base, le report du solde d'une semaine à l'autre et l'application des notes sans double traitement.

## Requirements

### Requirement: Solde en minutes entières
Le système SHALL tenir un solde en minutes entières, qui peut être négatif.

#### Scenario: Solde négatif autorisé
- **GIVEN** un solde de 10 minutes
- **WHEN** une note donne un débit de 50 minutes
- **THEN** le solde est de −40 minutes

### Requirement: Allocation à la création
Le système SHALL créditer, à la création du portefeuille, l'allocation de la semaine en cours, de sorte que le solde initial soit égal à l'allocation hebdomadaire.

#### Scenario: Création en milieu de semaine
- **WHEN** un portefeuille est créé un mercredi
- **THEN** son solde est de 240 minutes

### Requirement: Allocation hebdomadaire
Le système SHALL créditer 240 minutes à chaque lundi à 00h00 (heure locale) écoulé depuis la dernière allocation. Le montant SHALL être un paramètre de configuration.

#### Scenario: Passage au lundi
- **GIVEN** un portefeuille dont le dernier lundi crédité est le lundi précédent
- **WHEN** on met à jour le portefeuille à la date du lundi suivant, 00h00
- **THEN** 240 minutes sont créditées une seule fois

#### Scenario: Avant le lundi
- **WHEN** on met à jour le portefeuille le dimanche à 23h59
- **THEN** aucune allocation n'est créditée

#### Scenario: Plusieurs semaines manquées
- **GIVEN** un portefeuille non mis à jour pendant trois lundis
- **WHEN** on le met à jour
- **THEN** 3 × 240 minutes sont créditées

#### Scenario: Mise à jour répétée
- **WHEN** on met à jour deux fois de suite le portefeuille à la même date
- **THEN** la seconde mise à jour ne crédite rien

### Requirement: Report du solde
Le système SHALL reporter le solde d'une semaine à l'autre, qu'il soit positif ou négatif : l'allocation s'ajoute au solde existant et ne le remplace pas.

#### Scenario: Report positif
- **GIVEN** un solde de 100 minutes en fin de semaine
- **WHEN** le lundi suivant arrive
- **THEN** le solde est de 340 minutes

#### Scenario: Report négatif
- **GIVEN** un solde de −100 minutes en fin de semaine
- **WHEN** le lundi suivant arrive
- **THEN** le solde est de 140 minutes

### Requirement: Application d'une note au solde
Le système SHALL ajouter au solde le montant en minutes calculé pour une note (crédit si positif, débit si négatif), selon la spec `grade-conversion`. La date de la note n'influence pas le montant.

#### Scenario: Note créditante
- **GIVEN** un solde de 240 minutes
- **WHEN** une note de 15/20 en maths de coefficient 1 est appliquée
- **THEN** le solde est de 375 minutes

#### Scenario: Note débitante
- **GIVEN** un solde de 240 minutes
- **WHEN** une note de 8/20 en français de coefficient 1 est appliquée
- **THEN** le solde est de 0 minute

#### Scenario: Note sans effet
- **GIVEN** un solde de 240 minutes
- **WHEN** une note de 5/20 dans une matière non classée est appliquée
- **THEN** le solde reste de 240 minutes

### Requirement: Pas de double traitement d'une note
Le système SHALL identifier chaque note par un identifiant et SHALL ignorer toute note dont l'identifiant a déjà été appliqué, sans modifier le solde.

#### Scenario: Note reçue deux fois
- **GIVEN** une note d'identifiant « n-42 » déjà appliquée
- **WHEN** la même note est fournie à nouveau
- **THEN** le solde est inchangé

#### Scenario: Même identifiant, valeur différente
- **GIVEN** une note d'identifiant « n-42 » déjà appliquée avec 15/20
- **WHEN** une note d'identifiant « n-42 » avec 8/20 est fournie
- **THEN** elle est ignorée et le solde est inchangé

### Requirement: Note non numérique ignorée
Le système SHALL ignorer sans erreur une note dont la valeur n'est pas numérique (absent, dispensé, non noté, valeur vide), sans modifier le solde. L'identifiant d'une telle note n'est pas marqué comme traité : si une valeur numérique est fournie plus tard sous le même identifiant, elle est appliquée.

#### Scenario: Élève absent
- **GIVEN** un solde de 240 minutes
- **WHEN** une note dont la valeur est « Abs » est appliquée
- **THEN** aucune erreur n'est signalée et le solde reste de 240 minutes

#### Scenario: Valeur fournie après coup
- **GIVEN** une note d'identifiant « n-7 » ignorée parce que sa valeur était « Abs »
- **WHEN** la note d'identifiant « n-7 » est fournie à nouveau avec 15/20 en maths de coefficient 1
- **THEN** elle est appliquée et le solde augmente de 135 minutes

### Requirement: Rejet atomique d'une note invalide
Le système SHALL laisser le solde et la liste des notes déjà traitées inchangés lorsqu'une note est rejetée comme invalide.

#### Scenario: Note invalide
- **GIVEN** un solde de 240 minutes
- **WHEN** une note de 22/20 est appliquée
- **THEN** une erreur est signalée, le solde reste de 240 minutes et l'identifiant de la note n'est pas marqué comme traité
