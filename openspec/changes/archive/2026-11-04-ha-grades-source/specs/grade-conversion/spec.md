# Spec Delta

## MODIFIED Requirements

### Requirement: Multiplicateur par matière
Le système SHALL appliquer à chaque matière, identifiée par son nom d'EcoleDirecte (comparaison insensible à la casse, aux accents, à la ponctuation et aux espaces), un multiplicateur : MATHEMATIQUES 3, FRANCAIS 3, ANGLAIS LV1 3, ENS.INTEG.SC.&TECHNO 3, HISTOIRE-GEOGRAPHIE 2, EDUCATION MUSICALE 0,5, ARTS PLASTIQUES 0,5, ED PHYSIQUE & SPORT 0,5. Une matière absente de la table SHALL avoir un multiplicateur de 0 et être signalée à l'appelant. La table SHALL être un paramètre de configuration.

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

#### Scenario: Matière écrite avec de la ponctuation
- **WHEN** la matière « ed.physique & sport. » ou « ENS INTEG SC TECHNO » est recherchée
- **THEN** elle est reconnue comme « ED PHYSIQUE & SPORT » (multiplicateur 0,5) ou « ENS.INTEG.SC.&TECHNO » (multiplicateur 3)

#### Scenario: Matières voisines distinguées
- **WHEN** les matières « ANGLAIS LV1 » et « ANGLAIS LV2 » sont comparées
- **THEN** elles restent deux matières différentes
