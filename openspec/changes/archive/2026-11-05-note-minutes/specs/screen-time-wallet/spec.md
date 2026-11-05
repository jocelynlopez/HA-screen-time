# Spec Delta

## ADDED Requirements

### Requirement: Minutes apportées par chaque note
Le compte rendu du bilan SHALL donner, pour chaque note comptée dans la moyenne de la semaine, les minutes signées qu'elle apporte au crédit de semaine (poids × (note sur 20 − pivot) × taux × multiplicateurs ÷ max(poids total, poids minimal), arrondies à l'entier le plus proche, demi vers l'écart à zéro), ainsi que le capital reporté (avant le bilan) et un complément de la moyenne générale tels que reporté + minutes des notes + complément = temps disponible. Hors crédit de repli.

#### Scenario: Minutes de chaque note
- **GIVEN** sept moyennes habituelles
- **WHEN** un bilan compte arts plastiques 9/10 de coefficient 0,5 et français 7/20 de coefficient 1
- **THEN** le compte rendu donne +42 minutes pour arts plastiques et −415 pour français

#### Scenario: Somme exacte
- **GIVEN** le même bilan, avec un capital notes de 0 avant le bilan
- **WHEN** le compte rendu est lu
- **THEN** le complément vaut 227 et 0 + 42 − 415 + 227 = −146, le temps disponible

#### Scenario: Capital reporté
- **GIVEN** un capital notes de 145 avant le bilan
- **WHEN** le bilan est effectué
- **THEN** le compte rendu indique 145 minutes reportées et la somme reste égale au temps disponible

#### Scenario: Semaine sans note
- **WHEN** aucune note n'est comptée
- **THEN** le compte rendu n'a aucune minute par note et le complément vaut le crédit initial plus le crédit de semaine

#### Scenario: Semaine partiellement couverte
- **GIVEN** des notes dont le poids total est inférieur au poids minimal
- **WHEN** le bilan est effectué
- **THEN** le complément contient la part du crédit de semaine que couvre la moyenne générale

#### Scenario: Crédit de repli
- **WHEN** moins de quatre matières ont une moyenne
- **THEN** le compte rendu n'a ni minutes par note ni complément

#### Scenario: Note non significative ignorée
- **GIVEN** l'option qui ignore les notes non significatives et une note non significative
- **WHEN** le bilan est effectué
- **THEN** cette note n'a pas de minutes dans le compte rendu
