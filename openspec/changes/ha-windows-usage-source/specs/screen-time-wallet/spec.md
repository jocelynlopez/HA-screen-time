# Spec Delta

## ADDED Requirements

### Requirement: Regroupement des consommations automatiques
Le système SHALL, pour une consommation automatique, ajouter les minutes au dernier mouvement du journal quand celui-ci est une consommation de même motif datée du même jour, au lieu de créer un nouveau mouvement. Une consommation manuelle ou d'un autre motif ou d'un autre jour SHALL créer un mouvement distinct.

#### Scenario: Trois relevés dans la journée
- **GIVEN** un crédit hebdomadaire de 228 minutes
- **WHEN** 5, 3 puis 7 minutes sont consommées automatiquement le même jour avec le motif « PC de Mael »
- **THEN** le journal contient un seul mouvement de consommation de variation −15 sur le crédit hebdomadaire

#### Scenario: Jour différent
- **WHEN** une consommation automatique de même motif a lieu le lendemain
- **THEN** un nouveau mouvement est créé

#### Scenario: Motif différent
- **WHEN** une consommation automatique d'un autre capteur a lieu le même jour
- **THEN** un nouveau mouvement est créé

#### Scenario: Consommation manuelle
- **WHEN** une consommation manuelle suit une consommation automatique de même motif
- **THEN** elle crée son propre mouvement
