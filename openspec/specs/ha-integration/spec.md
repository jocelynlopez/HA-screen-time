# ha-integration Specification

## Purpose
Définit le comportement de l'intégration Home Assistant `screen_time_wallet` : création d'un portefeuille par enfant, paramètres modifiables dans l'interface, conservation de l'état, bilan automatique du lundi, entités, services et notifications qui exposent le portefeuille aux tableaux de bord et aux automatisations.

## Requirements

### Requirement: Un portefeuille par entrée de configuration
Le système SHALL créer un portefeuille par entrée de configuration, identifié par le nom de l'enfant saisi. Une entrée de même nom SHALL être refusée. Chaque entrée SHALL avoir son propre état, ses entités et ses paramètres.

#### Scenario: Création d'un portefeuille
- **WHEN** l'utilisateur ajoute l'intégration et saisit le nom « Mael »
- **THEN** une entrée est créée et un portefeuille neuf s'initialise avec un crédit hebdomadaire de 240 minutes et un capital notes de 0

#### Scenario: Nom en double
- **GIVEN** une entrée existante nommée « Mael »
- **WHEN** l'utilisateur ajoute une entrée nommée « Mael »
- **THEN** la création est refusée avec un message explicite

#### Scenario: Deux enfants indépendants
- **GIVEN** deux entrées « Mael » et « Lena »
- **WHEN** 60 minutes sont consommées sur le portefeuille de Mael
- **THEN** le portefeuille de Lena ne change pas

### Requirement: Options modifiables dans l'interface
Le système SHALL permettre de modifier depuis l'interface les paramètres de chaque portefeuille : temps maximal (heures), part des notes (%), pivot, poids minimal, nombre minimal de matières, crédit de repli, notes non significatives, rapport hebdomadaire, service de notification et capteur de notes EcoleDirecte. Une valeur incohérente SHALL être refusée et une modification SHALL s'appliquer sans perdre l'état.

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

### Requirement: Table des matières modifiable
Le système SHALL permettre d'ajouter, de modifier et de supprimer des matières dans la table des multiplicateurs depuis l'interface, la table par défaut étant préremplie. Une table dont la somme des multiplicateurs serait nulle SHALL être refusée.

#### Scenario: Ajout d'une matière
- **WHEN** la matière « TECHNOLOGIE » est ajoutée avec le multiplicateur 1
- **THEN** elle est reconnue et ses notes ont un poids

#### Scenario: Modification
- **WHEN** le multiplicateur de « HISTOIRE-GEOGRAPHIE » passe de 2 à 3
- **THEN** la table utilise 3 pour cette matière

#### Scenario: Suppression
- **WHEN** la matière « ED PHYSIQUE & SPORT » est supprimée
- **THEN** elle devient une matière inconnue

#### Scenario: Table vide refusée
- **WHEN** toutes les matières seraient supprimées
- **THEN** la modification est refusée

### Requirement: Persistance de l'état
Le système SHALL enregistrer l'état de chaque portefeuille (crédit hebdomadaire, capital notes, dernier bilan, notes déjà vues, journal des mouvements) dans le stockage de HA après chaque modification, et le restaurer au démarrage. Un stockage illisible SHALL empêcher le chargement de l'entrée sans être écrasé.

#### Scenario: Redémarrage
- **GIVEN** un portefeuille avec un crédit hebdomadaire de 128 et un capital notes de 100
- **WHEN** Home Assistant redémarre
- **THEN** l'entrée retrouve exactement ces valeurs

#### Scenario: Premier démarrage
- **WHEN** aucun état n'a encore été enregistré pour l'entrée
- **THEN** un portefeuille neuf est créé et enregistré

#### Scenario: Stockage illisible
- **WHEN** l'état enregistré est illisible
- **THEN** l'entrée n'est pas chargée, une erreur est journalisée et le stockage n'est pas écrasé

### Requirement: Bilan automatique du lundi
Le système SHALL effectuer le bilan de chaque portefeuille chaque lundi à 00h00 (heure locale de HA) et, au démarrage, effectuer les bilans des lundis manqués. L'état SHALL être enregistré après chaque bilan.

#### Scenario: Lundi à minuit
- **WHEN** le lundi 00h00 arrive
- **THEN** le bilan est effectué et l'état est enregistré

#### Scenario: Autre jour
- **WHEN** le déclencheur quotidien s'exécute un mercredi
- **THEN** aucun bilan n'est effectué

#### Scenario: Lundis manqués pendant un arrêt
- **GIVEN** Home Assistant arrêté pendant deux lundis
- **WHEN** il redémarre
- **THEN** deux bilans sont effectués

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

### Requirement: Capteurs du portefeuille
Le système SHALL exposer pour chaque portefeuille quatre capteurs : le temps disponible en minutes, le crédit hebdomadaire en minutes, le capital notes en minutes (négatif possible) et la date du dernier bilan. Ils SHALL se mettre à jour après chaque bilan, consommation ou ajustement.

#### Scenario: Temps disponible
- **GIVEN** un crédit hebdomadaire de 228 et un capital notes de −100
- **WHEN** le capteur « Temps disponible » est lu
- **THEN** il vaut 128 minutes

#### Scenario: Mise à jour après consommation
- **WHEN** 100 minutes sont consommées
- **THEN** les capteurs reflètent immédiatement le nouvel état

#### Scenario: Dernier bilan
- **WHEN** un bilan a été effectué le lundi 9 novembre
- **THEN** le capteur « Dernier bilan » indique cette date et expose en attributs le crédit initial et le crédit de semaine

### Requirement: Journal des mouvements exposé
Le système SHALL exposer en attribut du capteur « Dernier bilan » les 20 derniers mouvements du portefeuille, du plus récent au plus ancien, avec leur type, leur date, leur montant et leur motif.

#### Scenario: Plusieurs mouvements
- **GIVEN** un bilan, une consommation de 60 minutes et un ajustement de +30 minutes
- **WHEN** l'attribut du journal est lu
- **THEN** il liste l'ajustement, la consommation et le bilan dans cet ordre

#### Scenario: Journal limité
- **WHEN** plus de 20 mouvements existent
- **THEN** seuls les 20 plus récents sont exposés

### Requirement: Service de consommation
Le système SHALL fournir le service `screen_time_wallet.consume` qui débite un nombre de minutes strictement positif, avec un motif optionnel, du portefeuille désigné par le capteur « Temps disponible » : crédit hebdomadaire d'abord, puis capital notes.

#### Scenario: Consommation
- **GIVEN** un crédit hebdomadaire de 228 minutes
- **WHEN** le service est appelé avec 45 minutes et le motif « jeu console »
- **THEN** le crédit hebdomadaire vaut 183 minutes et un mouvement est journalisé avec ce motif

#### Scenario: Montant invalide
- **WHEN** le service est appelé avec 0 minute
- **THEN** l'appel est refusé et l'état ne change pas

### Requirement: Service d'ajustement manuel
Le système SHALL fournir le service `screen_time_wallet.adjust` qui ajoute au capital notes un nombre de minutes entier non nul, positif ou négatif, avec un motif optionnel, sur le portefeuille désigné par le capteur « Temps disponible ».

#### Scenario: Bonus parental
- **GIVEN** un capital notes de 100 minutes
- **WHEN** le service est appelé avec +30 minutes et le motif « aide aux devoirs »
- **THEN** le capital notes vaut 130 minutes

#### Scenario: Sanction
- **WHEN** le service est appelé avec −50 minutes
- **THEN** le capital notes diminue de 50 minutes

#### Scenario: Montant nul
- **WHEN** le service est appelé avec 0 minute
- **THEN** l'appel est refusé

### Requirement: Notifications
Le système SHALL créer une notification persistante de HA, propre à chaque portefeuille et mise à jour sans doublon, à l'issue d'un bilan qui rencontre une matière inconnue ou une note rejetée, en nommant les matières et les notes concernées. Si un service de notification est configuré, il SHALL recevoir le même message. Un bilan sans anomalie SHALL ne créer aucune notification d'anomalie.

#### Scenario: Matière inconnue
- **WHEN** un bilan rencontre une note de la matière « TECHNOLOGIE » absente de la table
- **THEN** une notification persistante nomme « TECHNOLOGIE » et invite à l'ajouter dans les options

#### Scenario: Note rejetée
- **WHEN** un bilan rejette une note de 22/20
- **THEN** la notification la mentionne avec le motif du rejet

#### Scenario: Service de notification configuré
- **GIVEN** le service `notify.mobile_app_telephone` configuré dans les options
- **WHEN** une notification est créée
- **THEN** ce service est appelé avec le même message

#### Scenario: Aucune anomalie
- **WHEN** un bilan ne rencontre ni matière inconnue ni note rejetée
- **THEN** aucune notification d'anomalie n'est créée

### Requirement: Rapport hebdomadaire
Le système SHALL, à l'issue de chaque bilan et si l'option est activée, publier un rapport qui détaille le calcul : le crédit initial avec la moyenne générale et le nombre de matières, le crédit de semaine avec la moyenne de la semaine, le poids des notes et chaque note comptée, puis le capital notes et le temps disponible. Le rapport est une notification persistante distincte de celle des anomalies, envoyée aussi au service de notification configuré.

#### Scenario: Contenu du rapport
- **GIVEN** un bilan avec sept moyennes et les notes arts plastiques 9/10 et français 7/20
- **WHEN** le rapport est publié
- **THEN** il indique la date du lundi, un crédit initial de 228 avec une moyenne générale d'environ 15,80 sur 7 matières, un crédit de semaine de −374 avec une moyenne de la semaine d'environ 7,85 pour un poids de 3,25, les deux notes comptées, le capital notes et le temps disponible

#### Scenario: Semaine sans note
- **WHEN** aucune note n'a été vue pendant la semaine
- **THEN** le rapport indique qu'aucune note n'a été comptée et que la moyenne générale a servi de moyenne de la semaine

#### Scenario: Crédit de repli
- **WHEN** moins de quatre matières ont une moyenne
- **THEN** le rapport indique que le crédit de repli est utilisé et que le crédit de semaine vaut 0

#### Scenario: Lundis manqués
- **GIVEN** trois lundis rattrapés au démarrage
- **WHEN** le rapport est publié
- **THEN** un seul message contient une section par lundi

#### Scenario: Service de notification
- **GIVEN** le service `notify.mobile_app_telephone` configuré
- **WHEN** le rapport est publié
- **THEN** ce service reçoit le même rapport

#### Scenario: Rapport désactivé
- **WHEN** l'option du rapport hebdomadaire est désactivée
- **THEN** aucun rapport n'est publié, mais les notifications d'anomalie restent actives

### Requirement: Traductions
Le système SHALL fournir en français et en anglais les textes des formulaires de configuration et d'options, des noms d'entités, des services et des messages d'erreur.

#### Scenario: Textes complets
- **WHEN** les fichiers de traduction sont comparés
- **THEN** le français et l'anglais ont exactement les mêmes clés

### Requirement: Métadonnées d'installation
Le système SHALL fournir un manifeste d'intégration valide (domaine `screen_time_wallet`, flux de configuration, mode de connexion calculé, version) et un fichier `hacs.json` à la racine du dépôt, pour une installation par HACS comme dépôt personnalisé.

#### Scenario: Manifeste valide
- **WHEN** le manifeste est lu
- **THEN** il déclare le domaine `screen_time_wallet`, un flux de configuration, une version et aucune dépendance Python à l'exécution

#### Scenario: Fichier HACS
- **WHEN** `hacs.json` est lu à la racine du dépôt
- **THEN** il est valide et nomme l'intégration

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
