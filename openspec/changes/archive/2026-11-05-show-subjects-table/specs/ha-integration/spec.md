# Spec Delta

## ADDED Requirements

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
