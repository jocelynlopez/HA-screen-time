# Spec Delta

## MODIFIED Requirements

### Requirement: Options modifiables dans l'interface
Le système SHALL permettre de modifier depuis l'interface les paramètres de chaque portefeuille : temps maximal en heures, part des notes en pourcentage, note pivot, poids minimal, nombre minimal de matières, crédit de repli en minutes, exclusion des notes non significatives, rapport hebdomadaire activé ou non, service de notification optionnel et capteur de notes EcoleDirecte optionnel. Une valeur incohérente SHALL être refusée. Une modification SHALL s'appliquer sans perdre l'état du portefeuille.

#### Scenario: Temps maximal en heures
- **WHEN** le temps maximal est saisi à 10 h
- **THEN** le portefeuille utilise un temps maximal de 600 minutes

#### Scenario: Part des notes en pourcentage
- **WHEN** la part des notes est saisie à 70
- **THEN** le portefeuille utilise une part de 0,7

#### Scenario: Valeur refusée
- **WHEN** le pivot est saisi à 20, ou la part des notes à 120
- **THEN** le formulaire est refusé avec un message d'erreur et les paramètres ne changent pas

#### Scenario: État conservé
- **GIVEN** un portefeuille avec un capital notes de 570 minutes
- **WHEN** un paramètre est modifié
- **THEN** le capital notes reste à 570 minutes

#### Scenario: Valeurs par défaut
- **WHEN** les options d'une nouvelle entrée sont affichées
- **THEN** elles valent 20 h, 60 %, pivot 12, poids minimal 3, 4 matières, repli 240 minutes, notes non significatives comptées, rapport hebdomadaire activé, aucun service de notification et aucun capteur de notes

#### Scenario: Choix du capteur de notes
- **WHEN** le capteur `sensor.ed_mael_lopez_notes` est choisi dans les options
- **THEN** le portefeuille utilise la source EcoleDirecte pour ce capteur

#### Scenario: Capteur de notes inexistant
- **WHEN** une entité qui n'existe pas est saisie comme capteur de notes
- **THEN** le formulaire est refusé avec un message d'erreur

#### Scenario: Retour sans source
- **WHEN** le capteur de notes est vidé dans les options
- **THEN** le portefeuille n'utilise plus de source et revient au crédit de repli

### Requirement: Source de moyennes et de notes
Le système SHALL obtenir les moyennes par matière et les notes visibles pour chaque bilan du capteur de notes EcoleDirecte choisi, ou d'une source vide à défaut, qui donne le crédit de repli et un crédit de semaine nul. Si la source échoue, le bilan SHALL ne pas être effectué et l'état rester inchangé ; une nouvelle tentative SHALL avoir lieu 5 minutes plus tard, jusqu'à 3 fois, puis au déclenchement quotidien suivant.

#### Scenario: Sans source
- **WHEN** un bilan est effectué sans source
- **THEN** le crédit hebdomadaire vaut 240 minutes et le capital notes ne change pas

#### Scenario: Source disponible
- **GIVEN** une source fournissant sept moyennes et des notes
- **WHEN** un bilan est effectué
- **THEN** le crédit initial et le crédit de semaine sont calculés à partir de ces données

#### Scenario: Source en erreur
- **WHEN** la source échoue pendant un bilan
- **THEN** le bilan n'est pas effectué, l'état ne change pas et le bilan est retenté

#### Scenario: Nouvelles tentatives
- **GIVEN** une source indisponible au démarrage de Home Assistant, un bilan étant dû
- **WHEN** 5 minutes s'écoulent puis que la source devient disponible
- **THEN** le bilan est effectué à cette nouvelle tentative

#### Scenario: Tentatives épuisées
- **WHEN** la source reste indisponible après 3 nouvelles tentatives
- **THEN** le bilan attend le déclenchement quotidien suivant

#### Scenario: Source EcoleDirecte
- **GIVEN** un capteur de notes EcoleDirecte et ses capteurs de matière
- **WHEN** un bilan est effectué
- **THEN** les moyennes et les notes lues dans ces capteurs servent au calcul

## ADDED Requirements

### Requirement: Source indisponible signalée
Le système SHALL créer une notification persistante, propre à chaque portefeuille et sans doublon, quand un bilan dû n'a pas pu être effectué parce que la source est indisponible, et SHALL la supprimer au bilan réussi suivant.

#### Scenario: Premier échec
- **WHEN** un bilan dû échoue parce que le capteur de notes est indisponible
- **THEN** une notification persistante signale la source indisponible

#### Scenario: Échecs répétés
- **WHEN** plusieurs tentatives échouent à la suite
- **THEN** une seule notification existe pour ce portefeuille

#### Scenario: Bilan réussi
- **GIVEN** une notification de source indisponible
- **WHEN** le bilan suivant réussit
- **THEN** la notification est supprimée

#### Scenario: Aucun bilan dû
- **WHEN** la source est indisponible alors qu'aucun bilan n'est dû
- **THEN** aucune notification n'est créée

### Requirement: Activation de la source
Le système SHALL activer la source quand un capteur de notes est choisi ou changé : les notes visibles sont mémorisées sans effet et le crédit hebdomadaire est remplacé par le crédit initial calculé sur les moyennes lues. Le capteur déjà activé SHALL ne pas être réactivé à un rechargement. Si la source n'est pas prête, l'activation SHALL être retentée comme un bilan.

#### Scenario: Première sélection
- **GIVEN** un portefeuille sans source et dix-huit notes visibles dans le capteur
- **WHEN** le capteur de notes est choisi
- **THEN** ces notes sont mémorisées sans effet et le crédit hebdomadaire est celui des moyennes lues

#### Scenario: Changement de capteur
- **WHEN** un autre capteur de notes est choisi
- **THEN** l'activation est refaite pour ce capteur

#### Scenario: Rechargement sans changement
- **WHEN** l'entrée est rechargée avec le même capteur de notes
- **THEN** l'activation n'est pas refaite

#### Scenario: Source pas prête
- **WHEN** le capteur choisi est indisponible au moment de l'activation
- **THEN** l'activation est retentée comme un bilan et le portefeuille reste inchangé en attendant

### Requirement: Ordre de chargement
Le système SHALL déclarer l'intégration EcoleDirecte (`ecole_directe`) comme dépendance de démarrage facultative, pour que ses capteurs soient chargés avant ceux du portefeuille sans l'imposer.

#### Scenario: Manifeste
- **WHEN** le manifeste est lu
- **THEN** il liste `ecole_directe` en `after_dependencies` et pas en `dependencies`
