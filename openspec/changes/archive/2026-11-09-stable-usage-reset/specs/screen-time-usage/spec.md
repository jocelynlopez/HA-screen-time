## MODIFIED Requirements

### Requirement: Remise à zéro du compteur
Le système SHALL traiter comme remise à zéro un relevé daté d'un autre jour que la référence : la référence repart de 0 et le relevé est consommé, sauf s'il est identique à la référence (relevé périmé : rien n'est consommé, la référence passe au nouveau jour). Un relevé du même jour inférieur à la référence SHALL être confirmé par un second relevé inférieur avant d'être consommé ; sans date, une baisse est une remise à zéro immédiate.

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

#### Scenario: Baisse confirmée le même jour
- **GIVEN** une référence de 190 minutes datée du 2026-11-07
- **WHEN** deux relevés successifs de 12 puis 14 minutes sont lus ce même jour
- **THEN** 14 minutes sont consommées au second relevé et la référence devient 14
