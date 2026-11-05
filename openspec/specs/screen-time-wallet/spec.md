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

### Requirement: Regroupement des consommations automatiques
Le système SHALL, pour une consommation automatique, ajouter les minutes au dernier mouvement du journal quand celui-ci est une consommation de même motif datée du même jour, au lieu de créer un nouveau mouvement. Une consommation manuelle ou d'un autre motif ou d'un autre jour SHALL créer un mouvement distinct.

#### Scenario: Trois relevés dans la journée
- **GIVEN** un crédit hebdomadaire de 228 minutes
- **WHEN** 5, 3 puis 7 minutes sont consommées automatiquement le même jour avec le motif « PC de Mael »
- **THEN** le journal contient un seul mouvement de consommation de variation −15 sur le crédit hebdomadaire

#### Scenario: Jour différent
- **WHEN** une consommation automatique de même motif a lieu le lendemain
- **THEN** un nouveau mouvement est créé

#### Scenario: Motif différent
- **WHEN** une consommation automatique d'un autre capteur a lieu le même jour
- **THEN** un nouveau mouvement est créé

#### Scenario: Consommation manuelle
- **WHEN** une consommation manuelle suit une consommation automatique de même motif
- **THEN** elle crée son propre mouvement

### Requirement: Origine des mouvements
Le système SHALL marquer comme automatique l'origine d'une consommation automatique dans le journal, et laisser sans origine les consommations et ajustements manuels. Le regroupement SHALL ne s'appliquer qu'à des mouvements automatiques : une consommation automatique SHALL créer son propre mouvement si le dernier mouvement est manuel, même de même motif.

#### Scenario: Consommation automatique marquée
- **WHEN** 5 minutes sont consommées automatiquement avec le motif « PC de Mael »
- **THEN** le mouvement du journal est marqué comme automatique

#### Scenario: Consommation manuelle sans origine
- **WHEN** 10 minutes sont consommées manuellement avec le motif « jeu console »
- **THEN** le mouvement du journal n'a pas d'origine automatique

#### Scenario: Ajustement sans origine
- **WHEN** un ajustement de 30 minutes est fait avec le motif « aide aux devoirs »
- **THEN** le mouvement du journal n'a pas d'origine automatique

#### Scenario: Automatique après manuelle de même motif
- **GIVEN** une consommation manuelle de motif « PC de Mael »
- **WHEN** une consommation automatique de même motif et du même jour a lieu
- **THEN** elle crée son propre mouvement

### Requirement: Mouvements de la semaine dans le compte rendu
Le système SHALL ajouter au compte rendu du bilan de chaque lundi les ajustements et consommations manuels de la semaine écoulée, avec leur date, leur variation du temps disponible et leur motif, ainsi que le total consommé automatiquement par motif. La semaine va du lundi 00h00 précédent à ce lundi 00h00, d'après les dates du journal.

#### Scenario: Mouvements manuels de la semaine
- **GIVEN** un ajustement de +30 le mercredi (« aide aux devoirs ») et une consommation de 45 le jeudi (« jeu console »)
- **WHEN** le bilan du lundi suivant est fait
- **THEN** le compte rendu liste ces deux mouvements dans l'ordre chronologique avec leur motif

#### Scenario: Total automatique par capteur
- **GIVEN** des consommations automatiques de 100 minutes pour « PC de Mael » et de 20 pour « Tablette » pendant la semaine
- **WHEN** le bilan est fait
- **THEN** le compte rendu donne 100 pour « PC de Mael » et 20 pour « Tablette »

#### Scenario: Semaine sans mouvement
- **WHEN** aucun mouvement manuel ni automatique n'a eu lieu pendant la semaine
- **THEN** le compte rendu ne contient aucune de ces listes

#### Scenario: Mouvement d'une autre semaine
- **GIVEN** un ajustement fait deux semaines avant le bilan
- **WHEN** le bilan est fait
- **THEN** il n'apparaît pas dans le compte rendu de cette semaine

#### Scenario: Plusieurs lundis rattrapés
- **GIVEN** deux lundis dus et un ajustement fait pendant la première des deux semaines
- **WHEN** les bilans sont faits ensemble
- **THEN** l'ajustement apparaît seulement dans le compte rendu de la première semaine

### Requirement: Prévision du prochain bilan
Le portefeuille SHALL pouvoir calculer, sans modifier son état, le compte rendu du bilan comme si le prochain lundi 00h00 était arrivé, à partir de la source des moyennes et des notes. Ce compte rendu SHALL inclure les mouvements de la semaine en cours. Les bilans déjà dus SHALL être rattrapés dans le calcul.

#### Scenario: Prévision sans effet
- **GIVEN** un portefeuille à jour un mercredi
- **WHEN** la prévision est calculée
- **THEN** le crédit hebdomadaire, le capital notes, le journal et les notes vues du portefeuille sont inchangés

#### Scenario: Notes pas encore comptées
- **GIVEN** une note de la semaine pas encore comptée
- **WHEN** la prévision est calculée
- **THEN** le compte rendu la compte et indique le capital et le temps disponible attendus au lundi

#### Scenario: Mouvements de la semaine
- **GIVEN** un ajustement et une consommation automatique pendant la semaine en cours
- **WHEN** la prévision est calculée
- **THEN** le compte rendu liste l'ajustement et le total automatique

#### Scenario: Bilan en retard
- **GIVEN** un lundi dont le bilan n'a pas été fait
- **WHEN** la prévision est calculée
- **THEN** elle rattrape ce lundi puis donne le résultat du prochain, sans modifier le portefeuille

#### Scenario: Prévision répétée
- **WHEN** la prévision est calculée deux fois de suite sans changement
- **THEN** les deux comptes rendus sont identiques

### Requirement: Minutes apportées par chaque note
Le compte rendu du bilan SHALL donner, pour chaque note comptée dans la moyenne de la semaine, les minutes signées qu'elle apporte au crédit de semaine (poids × (note sur 20 − pivot) × taux × multiplicateurs ÷ max(poids total, poids minimal), arrondies à l'entier le plus proche, demi vers l'écart à zéro), ainsi que le capital reporté (avant le bilan) et un complément de la moyenne générale tels que reporté + minutes des notes + complément = temps disponible. Hors crédit de repli.

#### Scenario: Minutes de chaque note
- **GIVEN** sept moyennes habituelles
- **WHEN** un bilan compte arts plastiques 9/10 de coefficient 0,5 et français 7/20 de coefficient 1
- **THEN** le compte rendu donne +42 minutes pour arts plastiques et −415 pour français

#### Scenario: Somme exacte
- **GIVEN** le même bilan, avec un capital notes de 0 avant le bilan
- **WHEN** le compte rendu est lu
- **THEN** le complément vaut 227 et 0 + 42 − 415 + 227 = −146, le temps disponible

#### Scenario: Capital reporté
- **GIVEN** un capital notes de 145 avant le bilan
- **WHEN** le bilan est effectué
- **THEN** le compte rendu indique 145 minutes reportées et la somme reste égale au temps disponible

#### Scenario: Semaine sans note
- **WHEN** aucune note n'est comptée
- **THEN** le compte rendu n'a aucune minute par note et le complément vaut le crédit initial plus le crédit de semaine

#### Scenario: Semaine partiellement couverte
- **GIVEN** des notes dont le poids total est inférieur au poids minimal
- **WHEN** le bilan est effectué
- **THEN** le complément contient la part du crédit de semaine que couvre la moyenne générale

#### Scenario: Crédit de repli
- **WHEN** moins de quatre matières ont une moyenne
- **THEN** le compte rendu n'a ni minutes par note ni complément

#### Scenario: Note non significative ignorée
- **GIVEN** l'option qui ignore les notes non significatives et une note non significative
- **WHEN** le bilan est effectué
- **THEN** cette note n'a pas de minutes dans le compte rendu

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
