# Spec Delta

## ADDED Requirements

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

## MODIFIED Requirements

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
