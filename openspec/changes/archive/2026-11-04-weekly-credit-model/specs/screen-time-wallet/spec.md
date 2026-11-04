# Spec Delta

## ADDED Requirements

### Requirement: Deux compartiments
Le système SHALL tenir un crédit hebdomadaire (entier supérieur ou égal à 0, non cumulable d'une semaine à l'autre) et un capital notes (entier, cumulable, qui peut être négatif). Le temps disponible SHALL être la somme des deux.

#### Scenario: Capital négatif
- **GIVEN** un crédit hebdomadaire de 228 minutes et un capital notes de −100 minutes
- **WHEN** le temps disponible est demandé
- **THEN** il est de 128 minutes

#### Scenario: Valeurs entières
- **WHEN** le portefeuille est lu
- **THEN** le crédit hebdomadaire et le capital notes sont des entiers de minutes

### Requirement: Initialisation du portefeuille
À sa création, le système SHALL fixer le crédit hebdomadaire au crédit initial de la semaine en cours, le capital notes à 0, et mémoriser toutes les notes déjà visibles comme déjà vues, sans effet sur les crédits.

#### Scenario: Création avec sept moyennes
- **WHEN** un portefeuille est créé un mercredi avec les sept moyennes qui donnent un crédit initial de 228 minutes
- **THEN** le crédit hebdomadaire est de 228, le capital notes de 0 et le temps disponible de 228

#### Scenario: Historique de notes visible à la création
- **WHEN** un portefeuille est créé alors que quinze notes sont déjà visibles
- **THEN** le capital notes reste à 0 et ces notes ne seront comptées dans aucun bilan

#### Scenario: Création avec moins de quatre matières
- **WHEN** un portefeuille est créé alors que deux matières seulement ont une moyenne
- **THEN** le crédit hebdomadaire est de 240 minutes

### Requirement: Bilan du lundi
Le système SHALL effectuer un bilan à chaque lundi 00h00 (heure locale) écoulé depuis le dernier bilan, à partir des moyennes par matière fournies par l'appelant : le crédit hebdomadaire est remplacé par le crédit initial, et le crédit de semaine des notes vues depuis le dernier bilan est ajouté au capital notes.

#### Scenario: Crédit hebdomadaire non cumulable
- **GIVEN** un crédit hebdomadaire de 228 minutes entièrement inutilisé
- **WHEN** le lundi suivant arrive et que le crédit initial est de 228
- **THEN** le crédit hebdomadaire est de 228 minutes, et non 456

#### Scenario: Capital cumulé
- **GIVEN** un capital notes de +111 minutes
- **WHEN** le bilan du lundi donne un crédit de semaine de +459 minutes
- **THEN** le capital notes est de +570 minutes

#### Scenario: Capital qui diminue
- **GIVEN** un capital notes de +1346 minutes
- **WHEN** le bilan du lundi donne un crédit de semaine de −374 minutes
- **THEN** le capital notes est de +972 minutes

#### Scenario: Avant le lundi
- **WHEN** le bilan est demandé le dimanche à 23h59
- **THEN** aucun bilan n'est effectué

#### Scenario: Bilan répété
- **WHEN** le bilan est demandé deux fois à la même date
- **THEN** le second appel ne modifie rien

### Requirement: Lundis manqués
Quand plusieurs lundis se sont écoulés depuis le dernier bilan, le système SHALL effectuer un bilan par lundi manqué : les notes en attente sont rattachées au premier, les suivants sont des semaines sans note, et le crédit hebdomadaire final est celui du dernier lundi.

#### Scenario: Trois lundis manqués
- **GIVEN** trois lundis écoulés depuis le dernier bilan, une moyenne générale de 15,796 et des notes en attente
- **WHEN** le bilan est demandé
- **THEN** le premier bilan utilise les notes en attente, les deux suivants ajoutent chacun le crédit de semaine d'une semaine sans note (+342 minutes), et le crédit hebdomadaire est celui d'une seule semaine

### Requirement: Notes de la semaine
Le système SHALL considérer comme notes de la semaine celles vues pour la première fois depuis le dernier bilan. Une note SHALL être identifiée par la date, la matière, le commentaire, le barème et le coefficient, à l'exclusion de sa valeur. Une note déjà vue SHALL être ignorée, même si sa valeur a changé.

#### Scenario: Note fournie deux fois
- **WHEN** la même note est fournie à deux relevés successifs
- **THEN** elle n'est comptée qu'une fois

#### Scenario: Valeur corrigée
- **GIVEN** une note déjà vue avec la valeur 15/20
- **WHEN** la même note est fournie avec la valeur 8/20
- **THEN** elle est ignorée et sa première valeur est conservée

#### Scenario: Deux notes proches distinguées par le commentaire
- **WHEN** deux notes de la même matière, du même jour, de même barème et de même coefficient ont pour commentaires « Attitude » et « Participation »
- **THEN** elles sont deux notes distinctes

#### Scenario: Note publiée en retard
- **WHEN** une note saisie la semaine précédente n'est vue pour la première fois qu'après le dernier bilan
- **THEN** elle est comptée dans le prochain bilan

### Requirement: Notes écartées ou signalées
Pendant un bilan, le système SHALL ignorer sans erreur une note non numérique et ne pas la marquer comme vue. Il SHALL rejeter une note invalide en la signalant et ne pas la marquer comme vue, sans interrompre le bilan. Une note d'une matière inconnue SHALL être sans effet, marquée comme vue et signalée.

#### Scenario: Élève absent
- **WHEN** une note dont la valeur est « Abs » est vue
- **THEN** elle n'a aucun effet et aucune erreur n'est signalée

#### Scenario: Valeur fournie après coup
- **GIVEN** une note ignorée parce que sa valeur était « Abs »
- **WHEN** la même note est fournie plus tard avec la valeur 15/20
- **THEN** elle est comptée dans le bilan suivant

#### Scenario: Note invalide
- **WHEN** une note de 22/20 est vue pendant un bilan
- **THEN** le bilan continue avec les autres notes, la note rejetée est signalée et n'est pas marquée comme vue

#### Scenario: Matière inconnue
- **WHEN** une note de « TECHNOLOGIE » est vue pendant un bilan
- **THEN** elle est sans effet sur les crédits, marquée comme vue et la matière est signalée dans le compte rendu

### Requirement: Compte rendu du bilan
Le système SHALL renvoyer à chaque bilan un compte rendu contenant le crédit initial, le crédit de semaine, les notes comptées, les notes rejetées et les matières inconnues.

#### Scenario: Compte rendu complet
- **WHEN** un bilan compte deux notes, rejette une note invalide et rencontre la matière « TECHNOLOGIE »
- **THEN** le compte rendu liste les deux notes comptées, la note rejetée et la matière inconnue, avec les deux crédits

### Requirement: Consommation
Le système SHALL débiter une consommation d'abord du crédit hebdomadaire, jusqu'à son épuisement, puis du capital notes, qui peut devenir négatif. Une consommation inférieure ou égale à 0 SHALL être rejetée avec une erreur.

#### Scenario: Consommation couverte par le crédit hebdomadaire
- **GIVEN** un crédit hebdomadaire de 228 minutes et un capital notes de 100
- **WHEN** 100 minutes sont consommées
- **THEN** le crédit hebdomadaire est de 128 et le capital notes reste à 100

#### Scenario: Consommation qui entame le capital
- **GIVEN** un crédit hebdomadaire de 228 minutes et un capital notes de 100
- **WHEN** 300 minutes sont consommées
- **THEN** le crédit hebdomadaire est de 0 et le capital notes de 28

#### Scenario: Capital qui devient négatif
- **GIVEN** un crédit hebdomadaire de 228 minutes et un capital notes de 0
- **WHEN** 300 minutes sont consommées
- **THEN** le crédit hebdomadaire est de 0 et le capital notes de −72

#### Scenario: Consommation invalide
- **WHEN** une consommation de 0 minute est demandée
- **THEN** une erreur est signalée et le portefeuille ne change pas

## REMOVED Requirements

### Requirement: Solde en minutes entières
**Reason**: Le solde unique est remplacé par deux compartiments.
**Migration**: Voir l'exigence « Deux compartiments ».

### Requirement: Allocation à la création
**Reason**: L'allocation fixe de 240 minutes est remplacée par le crédit initial issu des moyennes.
**Migration**: Voir l'exigence « Initialisation du portefeuille ».

### Requirement: Allocation hebdomadaire
**Reason**: L'allocation fixe du lundi est remplacée par le bilan du lundi.
**Migration**: Voir les exigences « Bilan du lundi » et « Lundis manqués ».

### Requirement: Report du solde
**Reason**: Seul le capital notes est reporté ; le crédit hebdomadaire n'est plus cumulable.
**Migration**: Voir les exigences « Deux compartiments » et « Bilan du lundi ».

### Requirement: Application d'une note au solde
**Reason**: Une note n'a plus d'effet direct sur le solde ; elle entre dans le crédit de semaine du bilan.
**Migration**: Voir l'exigence « Bilan du lundi » et la spec `weekly-credit`.

### Requirement: Pas de double traitement d'une note
**Reason**: L'identifiant de note fourni par l'appelant est remplacé par une clé calculée, car EcoleDirecte n'expose pas d'identifiant.
**Migration**: Voir l'exigence « Notes de la semaine ».

### Requirement: Note non numérique ignorée
**Reason**: Le comportement est repris dans le bilan, avec la reconnaissance d'une note non numérique dans `grade-conversion`.
**Migration**: Voir les exigences « Notes écartées ou signalées » et « Note non numérique » de `grade-conversion`.

### Requirement: Rejet atomique d'une note invalide
**Reason**: Une note invalide ne doit plus interrompre le bilan hebdomadaire : elle est rejetée et signalée, le reste est traité.
**Migration**: Voir l'exigence « Notes écartées ou signalées ».
