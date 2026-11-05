# Spec Delta

## ADDED Requirements

### Requirement: Commandes du portefeuille
Le système SHALL ajouter à l'appareil de chaque enfant une entité numérique « Minutes » (de 1 à 600, par pas de 5, 15 par défaut, valeur conservée au redémarrage) et deux boutons. « Ajouter du temps » ajuste le capital notes de la valeur choisie, « Retirer du temps » la consomme comme la consommation manuelle ; leur motif est « bouton ».

#### Scenario: Valeur par défaut
- **WHEN** un portefeuille est créé
- **THEN** l'entité « Minutes » vaut 15

#### Scenario: Ajouter du temps
- **GIVEN** un capital notes de 100 et l'entité « Minutes » à 30
- **WHEN** le bouton « Ajouter du temps » est pressé
- **THEN** le capital notes vaut 130, le temps disponible augmente de 30 et le journal contient un ajustement de motif « bouton »

#### Scenario: Retirer du temps
- **GIVEN** un crédit hebdomadaire de 228 et l'entité « Minutes » à 45
- **WHEN** le bouton « Retirer du temps » est pressé
- **THEN** le crédit hebdomadaire vaut 183 et le journal contient une consommation de motif « bouton »

#### Scenario: Retrait supérieur au temps disponible
- **GIVEN** un temps disponible de 10 minutes et l'entité « Minutes » à 30
- **WHEN** le bouton « Retirer du temps » est pressé
- **THEN** le capital notes vaut −20, comme pour la consommation manuelle

#### Scenario: Blocage déclenché par le bouton
- **GIVEN** un interrupteur de verrouillage choisi et un temps disponible de 15 minutes
- **WHEN** « Minutes » est réglée sur 15 et « Retirer du temps » pressé
- **THEN** l'interrupteur passe à l'état bloqué

#### Scenario: Valeur conservée au redémarrage
- **GIVEN** l'entité « Minutes » réglée sur 60
- **WHEN** Home Assistant redémarre
- **THEN** elle vaut encore 60

#### Scenario: Valeur hors limites
- **WHEN** la valeur 700 est demandée
- **THEN** elle est refusée par Home Assistant et la valeur précédente est gardée

#### Scenario: Appareil de l'enfant
- **WHEN** l'appareil du portefeuille est ouvert
- **THEN** l'entité « Minutes » et les deux boutons y apparaissent avec les capteurs
