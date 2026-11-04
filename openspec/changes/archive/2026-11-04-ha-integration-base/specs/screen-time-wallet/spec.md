# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

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
