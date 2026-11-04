# screen-time-wallet Specification

## Purpose

Définit le portefeuille de minutes de temps d'écran : son crédit hebdomadaire non cumulable et son capital notes durable, le bilan du lundi, le suivi des notes sans double traitement et la consommation.

## Requirements

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
Le système SHALL renvoyer à chaque bilan un compte rendu contenant le crédit initial, le crédit de semaine, les notes comptées, les notes rejetées et les matières inconnues, ainsi que les éléments du calcul : le nombre de matières avec moyenne, la moyenne générale, le poids total des notes de la semaine, la moyenne de la semaine, l'indication d'un crédit de repli, et le capital notes et le temps disponible après le bilan.

#### Scenario: Compte rendu complet
- **WHEN** un bilan compte deux notes, rejette une note invalide et rencontre la matière « TECHNOLOGIE »
- **THEN** le compte rendu liste les deux notes comptées, la note rejetée et la matière inconnue, avec les deux crédits

#### Scenario: Éléments du calcul
- **GIVEN** un portefeuille créé avec les sept moyennes habituelles (crédit hebdomadaire 228, capital notes 0)
- **WHEN** un bilan compte arts plastiques 9/10 de coefficient 0,5 et français 7/20 de coefficient 1
- **THEN** le compte rendu indique 7 matières avec moyenne, une moyenne générale d'environ 15,80, un poids total de 3,25, une moyenne de la semaine d'environ 7,85, un crédit initial de 228, un crédit de semaine de −374, un capital notes de −374 et un temps disponible de −146

#### Scenario: Crédit de repli
- **WHEN** un bilan est effectué avec moins de quatre matières ayant une moyenne
- **THEN** le compte rendu indique un crédit de repli, sans moyenne générale ni moyenne de la semaine, et un crédit de semaine de 0

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

### Requirement: Journal des mouvements
Le système SHALL consigner dans un journal chaque bilan, chaque consommation et chaque ajustement, avec son type, sa date, la variation du crédit hebdomadaire, la variation du capital notes et un motif. Le journal SHALL conserver au plus les 200 mouvements les plus récents.

#### Scenario: Bilan journalisé
- **GIVEN** un crédit hebdomadaire de 228 et un capital notes de 0
- **WHEN** un bilan donne un crédit initial de 218 et un crédit de semaine de +111
- **THEN** le journal contient un mouvement de type bilan avec une variation du crédit hebdomadaire de −10 et du capital notes de +111

#### Scenario: Consommation journalisée
- **WHEN** 45 minutes sont consommées avec le motif « jeu console »
- **THEN** le journal contient un mouvement de type consommation, de variation −45 sur le crédit hebdomadaire, avec ce motif

#### Scenario: Journal borné
- **WHEN** 250 mouvements ont eu lieu
- **THEN** le journal contient les 200 plus récents

### Requirement: Ajustement manuel
Le système SHALL permettre d'ajouter au capital notes un nombre de minutes entier non nul, positif ou négatif, avec un motif optionnel, sans toucher au crédit hebdomadaire. Un ajustement nul SHALL être rejeté avec une erreur.

#### Scenario: Ajustement positif
- **GIVEN** un capital notes de 100
- **WHEN** un ajustement de +30 est appliqué
- **THEN** le capital notes vaut 130 et le crédit hebdomadaire ne change pas

#### Scenario: Ajustement négatif
- **GIVEN** un capital notes de 20
- **WHEN** un ajustement de −50 est appliqué
- **THEN** le capital notes vaut −30

#### Scenario: Ajustement nul
- **WHEN** un ajustement de 0 est demandé
- **THEN** une erreur est signalée et le portefeuille ne change pas

### Requirement: État sérialisable
Le système SHALL exporter l'état du portefeuille (crédit hebdomadaire, capital notes, dernier bilan, notes déjà vues, journal) sous une forme compatible avec JSON et le restaurer à l'identique. Un état dont la version est inconnue SHALL être refusé avec une erreur.

#### Scenario: Aller-retour
- **GIVEN** un portefeuille ayant subi un bilan, une consommation et un ajustement
- **WHEN** son état est exporté puis restauré
- **THEN** le portefeuille restauré a le même crédit hebdomadaire, le même capital notes, le même dernier bilan, les mêmes notes vues et le même journal

#### Scenario: Notes déjà vues conservées
- **WHEN** l'état est restauré
- **THEN** une note déjà vue avant l'export n'est pas comptée de nouveau au bilan suivant

#### Scenario: Version inconnue
- **WHEN** un état de version inconnue est restauré
- **THEN** une erreur est signalée
