# Spec Delta

## MODIFIED Requirements

### Requirement: Activation de la source
Le système SHALL activer la source quand un capteur de notes est choisi ou changé : les notes visibles d'avant le lundi de la semaine en cours sont mémorisées sans effet, celles de la semaine en cours restent à compter, et le crédit hebdomadaire est remplacé par le crédit initial calculé sur les moyennes lues. Le capteur déjà activé SHALL ne pas être réactivé à un rechargement. Si la source n'est pas prête, l'activation SHALL être retentée comme un bilan.

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

#### Scenario: Notes de la semaine à l'activation
- **GIVEN** une note datée de cette semaine visible dans le capteur
- **WHEN** le capteur de notes est choisi
- **THEN** la prévision affiche cette note

## ADDED Requirements

### Requirement: Action de recomptage des notes
Le système SHALL fournir l'action `screen_time_wallet.recount_week`, sans paramètre, qui relit la source et rend à compter au prochain bilan les notes de la semaine en cours déjà mémorisées, puis enregistre l'état et rafraîchit la prévision. Elle SHALL refuser l'appel et ne rien changer si la source est inaccessible, et ne modifier ni les crédits ni le journal.

#### Scenario: Recomptage
- **GIVEN** deux notes de la semaine en cours mémorisées sans effet à l'activation
- **WHEN** l'action est appelée
- **THEN** la prévision affiche ces deux notes avec leurs minutes

#### Scenario: Source inaccessible
- **GIVEN** la source des notes échoue
- **WHEN** l'action est appelée
- **THEN** l'appel est refusé et l'état ne change pas

#### Scenario: Aucune note concernée
- **WHEN** l'action est appelée sans note de la semaine en cours
- **THEN** l'état enregistré ne change pas

#### Scenario: Crédits et journal inchangés
- **WHEN** l'action rend des notes à compter
- **THEN** le crédit hebdomadaire, le capital notes et le journal sont inchangés
