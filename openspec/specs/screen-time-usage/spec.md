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
Le système SHALL traiter comme remise à zéro un relevé daté d'un autre jour que la référence : la référence repart de 0 et le relevé est consommé, sauf s'il est identique à la référence (relevé périmé : rien n'est consommé, la référence passe au nouveau jour). Un relevé du même jour inférieur à la référence SHALL être ignoré, la référence gardant le maximum du jour (sauf juste après un relevé périmé, où la baisse est acceptée) ; sans date, une baisse est une remise à zéro immédiate.

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

#### Scenario: Relevé périmé au changement de jour
- **GIVEN** une référence de 40 minutes datée du 2026-11-06
- **WHEN** le relevé actuel est de 40 minutes, daté du 2026-11-07
- **THEN** aucune minute n'est consommée et la référence reste 40, datée du 2026-11-07

#### Scenario: Remise à zéro après un relevé périmé
- **GIVEN** la référence de 40 minutes devenue datée du 2026-11-07 par un relevé périmé
- **WHEN** le relevé suivant est de 3 minutes, daté du 2026-11-07
- **THEN** 3 minutes sont consommées et la référence devient 3

#### Scenario: Baisse passagère le même jour
- **GIVEN** une référence de 46 minutes datée du 2026-11-07
- **WHEN** un relevé de 36 minutes est suivi d'un relevé de 46 minutes, tous deux datés du 2026-11-07
- **THEN** aucune minute n'est consommée et la référence reste 46

#### Scenario: Compteur oscillant le même jour
- **GIVEN** une référence de 23 minutes datée du 2026-11-11
- **WHEN** les relevés 18, 18, 23, 18, 28 sont lus ce même jour
- **THEN** seules 5 minutes sont consommées (au relevé de 28) et la référence devient 28

#### Scenario: Baisse persistante le même jour
- **GIVEN** une référence de 190 minutes datée du 2026-11-07
- **WHEN** des relevés de 12 puis 14 minutes sont lus ce même jour
- **THEN** aucune minute n'est consommée et la référence reste 190

### Requirement: Relevé invalide ignoré
Le système SHALL ignorer un relevé inconnu, indisponible, vide, non numérique ou négatif, sans rien consommer ni modifier la référence.

#### Scenario: Capteur indisponible
- **GIVEN** une référence de 25 minutes
- **WHEN** l'état du capteur est « unavailable »
- **THEN** aucune minute n'est consommée et la référence reste 25

#### Scenario: Valeur négative
- **WHEN** le relevé est de −5 minutes
- **THEN** il est ignoré
