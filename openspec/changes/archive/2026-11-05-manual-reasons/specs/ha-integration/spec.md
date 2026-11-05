# Spec Delta

## ADDED Requirements

### Requirement: Mouvements manuels dans le rapport
Le système SHALL ajouter au rapport hebdomadaire une section « Mouvements manuels de la semaine » listant chaque ajustement et chaque consommation manuelle de la semaine écoulée (date, variation du temps disponible, motif ou « sans motif »), puis une ligne de consommation automatique par capteur. Les sections absentes de la semaine sont omises. Les actions `adjust` et `consume` alimentent cette section.

#### Scenario: Rapport avec mouvements manuels
- **GIVEN** un ajustement de +30 minutes (« aide aux devoirs ») et une consommation manuelle de 45 minutes (« jeu console ») pendant la semaine
- **WHEN** le rapport du lundi est publié
- **THEN** il liste les deux lignes avec leur date, +30 et −45 minutes et leur motif

#### Scenario: Mouvement sans motif
- **WHEN** un ajustement a été fait par l'action `adjust` sans champ `reason`
- **THEN** la ligne du rapport indique « sans motif »

#### Scenario: Consommation automatique
- **GIVEN** 312 minutes consommées automatiquement par « PC de Mael » pendant la semaine
- **WHEN** le rapport du lundi est publié
- **THEN** il contient une ligne « PC de Mael : 312 min »

#### Scenario: Aucun mouvement
- **WHEN** aucun mouvement n'a eu lieu pendant la semaine
- **THEN** le rapport ne contient pas la section des mouvements manuels

### Requirement: Entités de commande retirées
Le système SHALL supprimer du registre des entités, au démarrage, l'entité numérique « Minutes » et les boutons « Ajouter du temps » et « Retirer du temps » créés par les versions précédentes, pour ne pas laisser d'entités indisponibles. Les autres entités de l'appareil SHALL rester inchangées.

#### Scenario: Entités orphelines supprimées
- **GIVEN** le registre contient l'entité numérique et les deux boutons d'une version précédente
- **WHEN** l'entrée est chargée
- **THEN** ces trois entités sont supprimées du registre

#### Scenario: Autres entités conservées
- **WHEN** l'entrée est chargée
- **THEN** les quatre capteurs du portefeuille restent présents

### Requirement: Blueprints de script
Le dépôt SHALL fournir deux blueprints de script, « ajouter du temps » et « retirer du temps », qui demandent le capteur du portefeuille, des minutes (de 1 à 600) et une raison obligatoire, puis appellent respectivement l'action `adjust` et l'action `consume` avec ces valeurs. Le README SHALL proposer leur import.

#### Scenario: Ajouter du temps
- **WHEN** le blueprint « ajouter du temps » est lu
- **THEN** il demande un capteur du portefeuille, des minutes et une raison, et appelle `screen_time_wallet.adjust` avec les minutes et la raison saisies

#### Scenario: Retirer du temps
- **WHEN** le blueprint « retirer du temps » est lu
- **THEN** il appelle `screen_time_wallet.consume` avec les minutes et la raison saisies

#### Scenario: Raison obligatoire et minutes bornées
- **WHEN** les champs d'un blueprint sont lus
- **THEN** la raison est obligatoire et les minutes vont de 1 à 600

#### Scenario: Import depuis le README
- **WHEN** le README est lu
- **THEN** il donne pour chaque blueprint un lien d'import vers son URL brute

## REMOVED Requirements

### Requirement: Commandes du portefeuille
**Reason**: le script avec fenêtre de saisie (minutes et raison) est plus pratique que l'entité numérique et les deux boutons, et permet de justifier chaque mouvement.
**Migration**: importer les blueprints « ajouter du temps » et « retirer du temps » et créer un script depuis chacun ; les actions `screen_time_wallet.adjust` et `screen_time_wallet.consume` restent disponibles.
