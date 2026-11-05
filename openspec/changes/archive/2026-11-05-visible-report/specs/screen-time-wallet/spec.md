# Spec Delta

## ADDED Requirements

### Requirement: Prévision du prochain bilan
Le portefeuille SHALL pouvoir calculer, sans modifier son état, le compte rendu du bilan comme si le prochain lundi 00h00 était arrivé, à partir de la source des moyennes et des notes. Ce compte rendu SHALL inclure les mouvements de la semaine en cours. Les bilans déjà dus SHALL être rattrapés dans le calcul.

#### Scenario: Prévision sans effet
- **GIVEN** un portefeuille à jour un mercredi
- **WHEN** la prévision est calculée
- **THEN** le crédit hebdomadaire, le capital notes, le journal et les notes vues du portefeuille sont inchangés

#### Scenario: Notes pas encore comptées
- **GIVEN** une note de la semaine pas encore comptée
- **WHEN** la prévision est calculée
- **THEN** le compte rendu la compte et indique le capital et le temps disponible attendus au lundi

#### Scenario: Mouvements de la semaine
- **GIVEN** un ajustement et une consommation automatique pendant la semaine en cours
- **WHEN** la prévision est calculée
- **THEN** le compte rendu liste l'ajustement et le total automatique

#### Scenario: Bilan en retard
- **GIVEN** un lundi dont le bilan n'a pas été fait
- **WHEN** la prévision est calculée
- **THEN** elle rattrape ce lundi puis donne le résultat du prochain, sans modifier le portefeuille

#### Scenario: Prévision répétée
- **WHEN** la prévision est calculée deux fois de suite sans changement
- **THEN** les deux comptes rendus sont identiques
