# Spec Delta

## MODIFIED Requirements

### Requirement: Activation d'une source
Le système SHALL permettre d'activer une source de données sur un portefeuille existant : les notes visibles datées d'avant le lundi de la semaine en cours sont mémorisées comme déjà vues sans effet, celles de la semaine en cours restent à compter au prochain bilan, le crédit hebdomadaire est remplacé par le crédit initial calculé sur les moyennes fournies, et le capital notes et la date du dernier bilan ne changent pas. L'activation SHALL être journalisée.

#### Scenario: Notes visibles mémorisées
- **GIVEN** un portefeuille créé sans source
- **WHEN** une source est activée avec dix-huit notes visibles datées d'avant la semaine en cours
- **THEN** ces notes ne sont comptées dans aucun bilan ultérieur

#### Scenario: Crédit hebdomadaire remplacé
- **GIVEN** un crédit hebdomadaire de 240 minutes (repli) et un capital notes de 100
- **WHEN** une source est activée avec sept moyennes qui donnent un crédit initial de 228
- **THEN** le crédit hebdomadaire vaut 228, le capital notes reste à 100 et le journal contient un mouvement d'initialisation de variation −12 sur le crédit hebdomadaire

#### Scenario: Moins de quatre matières
- **WHEN** une source est activée avec trois moyennes seulement
- **THEN** le crédit hebdomadaire vaut le crédit de repli

#### Scenario: Notes de la semaine en cours conservées
- **GIVEN** une activation le jeudi avec une note datée du lundi et une note datée du mardi de la même semaine
- **WHEN** le bilan du lundi suivant est effectué
- **THEN** ces deux notes sont comptées

#### Scenario: Note d'une semaine précédente mémorisée
- **GIVEN** une activation le jeudi avec une note datée du dimanche précédent
- **WHEN** le bilan du lundi suivant est effectué
- **THEN** cette note n'est pas comptée

## ADDED Requirements

### Requirement: Recomptage des notes de la semaine
Le portefeuille SHALL pouvoir rendre à compter au prochain bilan les notes datées du lundi de la semaine en cours ou après, en les retirant des notes vues, et renvoyer leur nombre. Les notes d'avant ce lundi, les crédits, le capital et le journal ne changent pas.

#### Scenario: Notes rendues à compter
- **GIVEN** deux notes de la semaine en cours mémorisées comme vues
- **WHEN** le recomptage est demandé avec ces notes
- **THEN** le prochain bilan les compte et le recomptage renvoie 2

#### Scenario: Notes précédentes inchangées
- **GIVEN** une note d'une semaine précédente mémorisée comme vue
- **WHEN** le recomptage est demandé
- **THEN** cette note reste vue et n'est pas comptée

#### Scenario: Aucune note concernée
- **WHEN** aucune note n'est datée de la semaine en cours
- **THEN** le recomptage renvoie 0 et l'état ne change pas

#### Scenario: Crédits et journal inchangés
- **WHEN** des notes sont rendues à compter
- **THEN** le crédit hebdomadaire, le capital notes et le journal sont inchangés
