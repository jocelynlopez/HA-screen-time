# screen-time-usage Specification

## Purpose
Définit comment la consommation de temps d'écran est déduite des relevés successifs d'un compteur journalier en minutes, y compris au premier relevé, à la remise à zéro du compteur et pour les relevés invalides.

## Requirements

### Requirement: Consommation entre deux relevés
Le système SHALL calculer la consommation comme la partie entière de la différence entre le relevé actuel et le relevé de référence, puis avancer la référence du nombre de minutes consommées, de sorte que les fractions de minute ne soient ni perdues ni comptées deux fois.

#### Scenario: Usage normal
- **GIVEN** un relevé de référence de 10 minutes
- **WHEN** le relevé actuel est de 25 minutes
- **THEN** 15 minutes sont consommées et la référence devient 25

#### Scenario: Aucun usage
- **GIVEN** un relevé de référence de 25 minutes
- **WHEN** le relevé actuel est de 25 minutes
- **THEN** aucune minute n'est consommée

#### Scenario: Minutes fractionnaires
- **GIVEN** un relevé de référence de 10 minutes
- **WHEN** les relevés suivants sont 10,6 puis 11,2
- **THEN** le premier relevé ne consomme rien et laisse la référence à 10, puis le second consomme 1 minute et porte la référence à 11

### Requirement: Premier relevé
Le système SHALL prendre le premier relevé d'un compteur comme référence, avec sa date quand elle existe, sans rien consommer.

#### Scenario: Premier relevé en cours de journée
- **WHEN** le premier relevé est de 87 minutes
- **THEN** aucune minute n'est consommée et la référence devient 87

#### Scenario: Relevé suivant
- **GIVEN** la référence 87
- **WHEN** le relevé suivant est de 92 minutes
- **THEN** 5 minutes sont consommées

### Requirement: Remise à zéro du compteur
Le système SHALL traiter comme une remise à zéro du compteur un relevé daté d'un autre jour que la référence ou inférieur à la référence : la référence repart de 0 et le relevé actuel est la consommation depuis la remise à zéro, sans supposer l'heure de celle-ci.

#### Scenario: Changement de jour sans baisse
- **GIVEN** une référence de 190 minutes datée du 2026-11-04
- **WHEN** le relevé actuel est de 200 minutes, daté du 2026-11-05
- **THEN** 200 minutes sont consommées et la référence devient 200

#### Scenario: Baisse sans date
- **GIVEN** une référence de 190 minutes, sans date
- **WHEN** le relevé actuel est de 12 minutes, sans date
- **THEN** 12 minutes sont consommées et la référence devient 12

#### Scenario: Même jour
- **GIVEN** une référence de 12 minutes datée du 2026-11-04
- **WHEN** le relevé actuel est de 30 minutes, daté du 2026-11-04
- **THEN** 18 minutes sont consommées

#### Scenario: Remise à zéro exacte
- **GIVEN** une référence de 190 minutes
- **WHEN** le relevé actuel est de 0 minute
- **THEN** aucune minute n'est consommée et la référence devient 0

#### Scenario: Journée suivante
- **GIVEN** une référence de 12 minutes après une remise à zéro
- **WHEN** le relevé actuel est de 30 minutes
- **THEN** 18 minutes sont consommées

### Requirement: Relevé invalide ignoré
Le système SHALL ignorer un relevé inconnu, indisponible, vide, non numérique ou négatif, sans rien consommer ni modifier la référence.

#### Scenario: Capteur indisponible
- **GIVEN** une référence de 25 minutes
- **WHEN** l'état du capteur est « unavailable »
- **THEN** aucune minute n'est consommée et la référence reste 25

#### Scenario: Valeur négative
- **WHEN** le relevé est de −5 minutes
- **THEN** il est ignoré
