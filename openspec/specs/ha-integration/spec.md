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
Le système SHALL permettre d'ajouter, de modifier et de supprimer des matières dans la table des multiplicateurs depuis l'interface, la table par défaut étant préremplie et complétée automatiquement. Une matière supprimée qui existe encore dans la source SHALL être rajoutée avec le multiplicateur 1 ; le multiplicateur 0 l'exclut du calcul. Une table dont la somme des multiplicateurs serait nulle SHALL être refusée.

#### Scenario: Ajout d'une matière
- **WHEN** la matière « TECHNOLOGIE » est ajoutée avec le multiplicateur 1
- **THEN** elle est reconnue et ses notes ont un poids

#### Scenario: Modification
- **WHEN** le multiplicateur de « HISTOIRE-GEOGRAPHIE » passe de 2 à 3
- **THEN** la table utilise 3 pour cette matière

#### Scenario: Suppression
- **WHEN** la matière « LATIN », absente de la source, est supprimée
- **THEN** elle n'est plus dans la table et n'est pas rajoutée

#### Scenario: Matière supprimée mais présente dans la source
- **WHEN** la matière « ED PHYSIQUE & SPORT », publiée par la source, est supprimée
- **THEN** elle est rajoutée avec le multiplicateur 1 au prochain ajout automatique

#### Scenario: Matière exclue
- **WHEN** le multiplicateur de « ED PHYSIQUE & SPORT » passe à 0
- **THEN** la matière reste dans la table et n'a aucun effet sur les crédits

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
Le système SHALL créer une notification persistante de HA, propre à chaque portefeuille et mise à jour sans doublon, à l'issue d'un bilan qui rejette une note, en nommant les notes concernées. Si un service de notification est configuré, il SHALL recevoir le même message. Un bilan sans note rejetée SHALL ne créer aucune notification d'anomalie.

#### Scenario: Matière inconnue
- **WHEN** un bilan rencontre une note de la matière « TECHNOLOGIE » absente de la table
- **THEN** la matière est ajoutée automatiquement et aucune notification d'anomalie n'est créée

#### Scenario: Note rejetée
- **WHEN** un bilan rejette une note de 22/20
- **THEN** la notification la mentionne avec le motif du rejet

#### Scenario: Service de notification configuré
- **GIVEN** le service `notify.mobile_app_telephone` configuré dans les options
- **WHEN** une notification est créée
- **THEN** ce service est appelé avec le même message

#### Scenario: Aucune anomalie
- **WHEN** un bilan ne rejette aucune note
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

### Requirement: Capteurs de temps d'écran
Le système SHALL permettre de choisir dans les options un ou plusieurs capteurs de temps d'écran, dont le relevé est le temps utilisé dans la journée : l'attribut `total_seconds` divisé par 60 quand il est numérique, sinon l'état en minutes. L'attribut `date`, s'il existe, est le jour du relevé. Une entité inexistante SHALL être refusée. L'ajout d'un capteur SHALL prendre son relevé actuel pour référence, et le retrait SHALL oublier sa référence. Par défaut, aucun capteur n'est choisi.

#### Scenario: Choix d'un capteur
- **WHEN** le capteur `sensor.pc_mael_screen_time` est choisi dans les options
- **THEN** le portefeuille le suit et prend son relevé actuel pour référence, sans rien consommer

#### Scenario: Entité inexistante
- **WHEN** une entité qui n'existe pas est saisie
- **THEN** le formulaire est refusé avec un message d'erreur

#### Scenario: Aucun capteur par défaut
- **WHEN** aucun capteur n'est choisi
- **THEN** aucune consommation automatique n'a lieu

#### Scenario: Capteur retiré puis rajouté
- **WHEN** un capteur est retiré des options puis rajouté plus tard
- **THEN** son relevé du moment est une nouvelle référence

### Requirement: Consommation automatique
Le système SHALL consommer automatiquement, à chaque nouveau relevé d'un capteur de temps d'écran choisi, la consommation calculée depuis son relevé de référence, avec pour motif le nom du capteur. Les consommations de plusieurs capteurs s'additionnent. L'état SHALL être enregistré et les entités mises à jour après chaque consommation.

#### Scenario: Consommation d'un relevé
- **GIVEN** un capteur à 10 minutes pris pour référence et un crédit hebdomadaire de 228
- **WHEN** le capteur passe à 25 minutes
- **THEN** le crédit hebdomadaire vaut 213, les capteurs du portefeuille sont mis à jour et le journal mentionne le capteur

#### Scenario: Relevé en secondes
- **GIVEN** un capteur dont l'attribut `total_seconds` vaut 660 et dont l'état vaut 10
- **WHEN** le relevé est lu
- **THEN** il vaut 11 minutes

#### Scenario: Deux capteurs
- **GIVEN** deux capteurs de temps d'écran
- **WHEN** le premier augmente de 15 minutes et le second de 20
- **THEN** 35 minutes sont consommées au total

#### Scenario: Relevé indisponible
- **WHEN** le capteur passe à « unavailable »
- **THEN** rien n'est consommé et la référence est conservée

#### Scenario: Remise à zéro du compteur
- **GIVEN** une référence de 190 minutes
- **WHEN** le capteur passe à 12 minutes
- **THEN** 12 minutes sont consommées

#### Scenario: Changement de jour
- **GIVEN** une référence de 190 minutes datée du 2026-11-04
- **WHEN** le capteur passe à 8 minutes, daté du 2026-11-05
- **THEN** 8 minutes sont consommées

#### Scenario: Usage supérieur au crédit
- **GIVEN** un crédit hebdomadaire de 10 minutes et un capital notes de 0
- **WHEN** 25 minutes sont consommées automatiquement
- **THEN** le crédit hebdomadaire vaut 0 et le capital notes −15

### Requirement: Relevés de référence conservés
Le système SHALL enregistrer les relevés de référence, valeur et date, avec l'état du portefeuille et les restaurer au démarrage, puis relever chaque capteur au démarrage pour consommer la différence survenue pendant l'arrêt. Un rechargement dû à une modification d'options SHALL ne pas refaire les références des capteurs inchangés.

#### Scenario: Redémarrage
- **GIVEN** une référence enregistrée de 25 minutes
- **WHEN** Home Assistant redémarre et que le capteur affiche 40 minutes
- **THEN** 15 minutes sont consommées

#### Scenario: Remise à zéro pendant l'arrêt
- **GIVEN** une référence enregistrée de 190 minutes
- **WHEN** Home Assistant redémarre et que le capteur affiche 12 minutes
- **THEN** 12 minutes sont consommées

#### Scenario: Changement de jour pendant l'arrêt
- **GIVEN** une référence enregistrée de 190 minutes datée du 2026-11-04
- **WHEN** Home Assistant redémarre et que le capteur affiche 200 minutes, daté du 2026-11-05
- **THEN** 200 minutes sont consommées

#### Scenario: Rechargement par les options
- **WHEN** une autre option est modifiée alors qu'un capteur de temps d'écran est suivi
- **THEN** sa référence est conservée et aucune minute n'est consommée deux fois

### Requirement: Ajout automatique des matières
Le système SHALL, à l'activation d'une source et avant chaque bilan, ajouter aux options, avec le multiplicateur 1 et le nom écrit par la source, chaque matière des données de la source absente de la table, puis l'utiliser dans ce calcul. Une matière déjà présente, même à 0, SHALL rester inchangée. Une notification persistante SHALL nommer les matières ajoutées, avec le même message pour le service de notification configuré.

#### Scenario: Matière détectée dans une moyenne
- **GIVEN** une table sans « TECHNOLOGIE » et un capteur de moyenne de cette matière à 14
- **WHEN** la source est activée
- **THEN** « TECHNOLOGIE » est ajoutée avec le multiplicateur 1 et le crédit initial la compte

#### Scenario: Matière détectée dans une note
- **GIVEN** une table sans « TECHNOLOGIE » et une note de cette matière
- **WHEN** un bilan est dû
- **THEN** la matière est ajoutée avant le calcul et la note compte avec le poids du multiplicateur 1

#### Scenario: Matière sans moyenne
- **WHEN** un capteur de matière absente de la table n'a pas encore de moyenne
- **THEN** la matière est ajoutée avec le multiplicateur 1

#### Scenario: Matière existante inchangée
- **GIVEN** « HISTOIRE-GEOGRAPHIE » à 2 et « MUSIQUE » à 0 dans la table
- **WHEN** la source publie ces deux matières
- **THEN** leurs multiplicateurs restent 2 et 0 et rien n'est ajouté

#### Scenario: Orthographe différente
- **GIVEN** « TECHNOLOGIE » dans la table
- **WHEN** la source publie « Technologie »
- **THEN** la matière est reconnue et n'est pas ajoutée une seconde fois

#### Scenario: Matière modifiable ensuite
- **GIVEN** « TECHNOLOGIE » ajoutée automatiquement
- **WHEN** son multiplicateur est changé en 2 dans les options
- **THEN** le calcul utilise 2

#### Scenario: Notification à l'ajout
- **GIVEN** le service `notify.mobile_app_telephone` configuré
- **WHEN** « TECHNOLOGIE » et « LATIN » sont ajoutées
- **THEN** une notification persistante les nomme et invite à régler leur multiplicateur, et le service reçoit le même message

#### Scenario: Aucune matière à ajouter
- **WHEN** toutes les matières de la source sont déjà dans la table
- **THEN** les options sont inchangées et aucune notification d'ajout n'est créée

### Requirement: Détection des matières à la demande
Le système SHALL proposer, dans la fenêtre des matières des options, une case « Détecter les matières de la source » qui, une fois cochée, lance la même détection que l'automatique sans exiger de nom de matière, puis affiche les matières ajoutées. La détection à la demande ne crée pas de notification persistante et ne recalcule pas le crédit hebdomadaire en cours.

#### Scenario: Détection à la demande
- **GIVEN** une source qui publie « TECHNOLOGIE », absente de la table
- **WHEN** la case est cochée et le formulaire envoyé
- **THEN** la matière est ajoutée avec le multiplicateur 1, la fenêtre la nomme et aucune notification persistante n'est créée

#### Scenario: Nom non exigé
- **WHEN** la case est cochée et le champ matière laissé vide
- **THEN** le formulaire est accepté

#### Scenario: Aucune matière à ajouter
- **WHEN** toutes les matières de la source sont déjà dans la table
- **THEN** la fenêtre l'indique et les options restent inchangées

#### Scenario: Source indisponible
- **WHEN** le capteur de notes est indisponible au moment de la détection
- **THEN** un message d'erreur s'affiche et les options restent inchangées

#### Scenario: Aucune source choisie
- **WHEN** aucun capteur de notes n'est choisi dans les options
- **THEN** la fenêtre indique qu'il faut en choisir un

#### Scenario: Case décochée
- **WHEN** la case n'est pas cochée et le champ matière est vide
- **THEN** le formulaire est refusé : le nom de la matière reste obligatoire

### Requirement: Table des matières visible
Le système SHALL afficher la table des matières courante, une ligne par matière avec son multiplicateur, triée par ordre alphabétique sans tenir compte de la casse ni des accents : au-dessus du formulaire de l'écran des matières, dans le message de fin de la détection à la demande et dans la notification des matières ajoutées automatiquement. L'affichage SHALL refléter les matières qui viennent d'être ajoutées ou modifiées.

#### Scenario: Écran des matières
- **GIVEN** une table avec « MATHEMATIQUES » à 3 et « EDUCATION MUSICALE » à 0,5
- **WHEN** l'écran des matières est ouvert
- **THEN** il affiche les deux lignes au-dessus du formulaire, « EDUCATION MUSICALE » avant « MATHEMATIQUES »

#### Scenario: Table mise à jour
- **WHEN** le multiplicateur de « MATHEMATIQUES » passe de 3 à 2 puis que l'écran est rouvert
- **THEN** la ligne de « MATHEMATIQUES » affiche 2

#### Scenario: Détection à la demande avec ajout
- **WHEN** la détection à la demande ajoute « TECHNOLOGIE »
- **THEN** le message nomme « TECHNOLOGIE » et affiche la table, qui contient la nouvelle ligne avec le multiplicateur 1

#### Scenario: Aucune nouvelle matière
- **WHEN** la détection à la demande ne trouve aucune nouvelle matière
- **THEN** le message l'indique et affiche la table courante

#### Scenario: Notification d'ajout
- **WHEN** des matières sont ajoutées automatiquement
- **THEN** la notification persistante, et le message du service de notification configuré, contiennent la table courante

#### Scenario: Écriture des nombres
- **WHEN** la table contient les multiplicateurs 3 et 0,5
- **THEN** le texte français affiche « 3 » et « 0,5 » et le texte anglais « 3 » et « 0.5 »

### Requirement: Interrupteurs de blocage
Le système SHALL permettre de choisir dans les options deux listes d'interrupteurs : des interrupteurs de verrouillage, bloqués à l'état ON, et des interrupteurs d'autorisation, bloqués à l'état OFF. Une entité inexistante SHALL être refusée. Par défaut, les deux listes sont vides et rien n'est piloté.

#### Scenario: Choix d'un interrupteur de verrouillage
- **WHEN** `switch.mael_lock` est choisi comme interrupteur de verrouillage
- **THEN** le portefeuille le pilote

#### Scenario: Choix d'un interrupteur d'autorisation
- **WHEN** `switch.mael_internet` est choisi comme interrupteur d'autorisation
- **THEN** le portefeuille le pilote avec le sens inverse

#### Scenario: Entité inexistante
- **WHEN** une entité qui n'existe pas est saisie
- **THEN** le formulaire est refusé avec un message d'erreur

#### Scenario: Aucun interrupteur par défaut
- **WHEN** les deux listes sont vides
- **THEN** aucun interrupteur n'est piloté et l'utilisateur peut verrouiller à la main

### Requirement: Blocage automatique
Le système SHALL mettre chaque interrupteur choisi à l'état « bloqué » quand le temps disponible est inférieur ou égal à 0 et à l'état « libre » quand il est strictement positif. Il SHALL remettre l'état en accord à chaque relevé d'un capteur de temps d'écran, au démarrage et après un bilan, une consommation ou un ajustement, sans rien changer tant qu'un bilan est dû.

#### Scenario: Temps épuisé
- **GIVEN** un temps disponible de 5 minutes et un interrupteur de verrouillage à OFF
- **WHEN** 5 minutes sont consommées
- **THEN** l'interrupteur passe à ON

#### Scenario: Interrupteur d'autorisation
- **GIVEN** un interrupteur d'autorisation à ON et un temps disponible épuisé
- **WHEN** l'état est remis en accord
- **THEN** l'interrupteur passe à OFF

#### Scenario: Temps rendu
- **GIVEN** un temps épuisé et un interrupteur de verrouillage à ON
- **WHEN** un ajustement de 30 minutes est fait
- **THEN** l'interrupteur repasse à OFF

#### Scenario: Recharge du lundi
- **GIVEN** un temps épuisé et un interrupteur de verrouillage à ON
- **WHEN** le bilan du lundi rend le temps disponible positif
- **THEN** l'interrupteur repasse à OFF

#### Scenario: Déblocage manuel annulé
- **GIVEN** un temps épuisé et un interrupteur de verrouillage remis à OFF à la main
- **WHEN** le capteur de temps d'écran donne un nouveau relevé
- **THEN** l'interrupteur repasse à ON

#### Scenario: Plusieurs interrupteurs
- **GIVEN** un interrupteur de verrouillage et un d'autorisation
- **WHEN** le temps disponible devient nul
- **THEN** le premier passe à ON et le second à OFF

#### Scenario: Interrupteur déjà dans l'état voulu
- **WHEN** l'état voulu est déjà celui de l'interrupteur
- **THEN** aucun service n'est appelé

#### Scenario: Interrupteur indisponible
- **WHEN** un interrupteur est « unavailable » ou « unknown »
- **THEN** rien n'est appelé pour lui et il est réessayé au relevé suivant

#### Scenario: Bilan dû
- **GIVEN** un bilan du lundi dû que la source en panne empêche
- **WHEN** l'état est remis en accord
- **THEN** aucun interrupteur ne change

### Requirement: Échec du blocage signalé
Le système SHALL créer une notification persistante propre au portefeuille quand le basculement d'un interrupteur échoue, en nommant l'interrupteur, la réessayer au prochain relevé et la supprimer dès que le basculement réussit.

#### Scenario: Basculement en échec
- **WHEN** l'appel du service pour `switch.mael_lock` lève une erreur
- **THEN** une notification persistante nomme l'interrupteur et le basculement est réessayé au relevé suivant

#### Scenario: Succès après échec
- **GIVEN** une notification d'échec pour `switch.mael_lock`
- **WHEN** le basculement réussit
- **THEN** la notification est supprimée

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

### Requirement: Capteur Rapport
Le système SHALL ajouter à l'appareil de l'enfant un capteur « Rapport » dont l'état est la date du dernier bilan (inconnu avant le premier) et dont les attributs contiennent le texte Markdown du dernier rapport du lundi (`last_report`), des 12 rapports précédents (`history`, du plus récent au plus ancien) et de la prévision du prochain bilan (`forecast`). Ses attributs SHALL être exclus de l'historique. Le README SHALL donner un exemple de carte Markdown.

#### Scenario: Attributs disponibles
- **GIVEN** un bilan effectué et une source disponible
- **WHEN** l'état du capteur est lu
- **THEN** son état est la date du bilan et ses attributs `last_report` et `forecast` contiennent du texte

#### Scenario: Historique exposé
- **GIVEN** quinze rapports du lundi conservés
- **WHEN** l'état du capteur est lu
- **THEN** `last_report` est le plus récent et `history` contient les 12 suivants, du plus récent au plus ancien

#### Scenario: Avant le premier bilan
- **GIVEN** aucun bilan n'a eu lieu depuis l'installation
- **WHEN** l'état du capteur est lu
- **THEN** son état est inconnu et `last_report` contient « Aucun rapport pour le moment »

#### Scenario: Rapport sans notification
- **GIVEN** le rapport hebdomadaire par notification est désactivé
- **WHEN** un bilan a lieu
- **THEN** `last_report` contient quand même le rapport de ce bilan

### Requirement: Historique des rapports
Le système SHALL enregistrer avec l'état chaque rapport du lundi, un par lundi traité, et les restituer après un redémarrage, dans la limite des 52 plus récents. La prévision SHALL NOT être enregistrée. Un état enregistré sans historique SHALL rester valide.

#### Scenario: Rapports après redémarrage
- **GIVEN** deux bilans ont produit deux rapports
- **WHEN** l'entrée est rechargée
- **THEN** `last_report` et `history` contiennent les mêmes textes

#### Scenario: Lundis rattrapés
- **GIVEN** deux lundis traités en une fois
- **WHEN** le bilan est terminé
- **THEN** les deux rapports sont conservés, `last_report` étant celui du lundi le plus récent

#### Scenario: Limite de l'historique
- **GIVEN** 52 rapports conservés
- **WHEN** un nouveau bilan a lieu
- **THEN** le plus ancien est supprimé et 52 rapports restent

#### Scenario: Prévision non enregistrée
- **WHEN** la prévision est recalculée puis l'entrée rechargée
- **THEN** l'état enregistré ne contient aucune prévision

#### Scenario: Ancien état
- **GIVEN** un état enregistré par une version précédente, sans rapport
- **WHEN** l'entrée est chargée
- **THEN** elle démarre sans erreur et `last_report` indique qu'il n'y a pas de rapport

### Requirement: Prévision du rapport
Le système SHALL calculer l'attribut `forecast` avec la prévision du portefeuille, titrée comme une prévision du prochain lundi « si rien ne change d'ici là », au chargement, après chaque mouvement ou bilan et à chaque changement du capteur de notes. Si la source est inaccessible, la prévision SHALL se limiter aux mouvements de la semaine avec une mention d'indisponibilité, sans notification d'erreur ni modification de l'état.

#### Scenario: Prévision mise à jour par un mouvement
- **WHEN** un ajustement de +30 minutes est fait
- **THEN** `forecast` contient ce mouvement et le temps disponible attendu au lundi

#### Scenario: Changement du capteur de notes
- **WHEN** le capteur de notes passe à un état contenant une nouvelle note
- **THEN** `forecast` en tient compte

#### Scenario: Source inaccessible
- **GIVEN** la source des notes échoue
- **WHEN** la prévision est calculée
- **THEN** `forecast` liste les mouvements de la semaine et indique que la prévision est indisponible, sans notification d'erreur

#### Scenario: État inchangé
- **WHEN** la prévision est recalculée
- **THEN** le portefeuille enregistré n'est pas modifié
