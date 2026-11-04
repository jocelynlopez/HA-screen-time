# Spec Delta

## ADDED Requirements

### Requirement: Activation d'une source
Le système SHALL permettre d'activer une source de données sur un portefeuille existant : toutes les notes alors visibles sont mémorisées comme déjà vues sans effet, le crédit hebdomadaire est remplacé par le crédit initial calculé à partir des moyennes fournies, et le capital notes et la date du dernier bilan ne changent pas. L'activation SHALL être journalisée.

#### Scenario: Notes visibles mémorisées
- **GIVEN** un portefeuille créé sans source
- **WHEN** une source est activée avec dix-huit notes visibles
- **THEN** ces notes ne sont comptées dans aucun bilan ultérieur

#### Scenario: Crédit hebdomadaire remplacé
- **GIVEN** un crédit hebdomadaire de 240 minutes (repli) et un capital notes de 100
- **WHEN** une source est activée avec sept moyennes qui donnent un crédit initial de 228
- **THEN** le crédit hebdomadaire vaut 228, le capital notes reste à 100 et le journal contient un mouvement d'initialisation de variation −12 sur le crédit hebdomadaire

#### Scenario: Moins de quatre matières
- **WHEN** une source est activée avec trois moyennes seulement
- **THEN** le crédit hebdomadaire vaut le crédit de repli
