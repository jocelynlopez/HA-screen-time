## MODIFIED Requirements

### Requirement: Mouvements de la semaine dans le compte rendu
Le système SHALL ajouter au compte rendu du bilan de chaque lundi tous les ajustements et consommations manuels de la semaine écoulée, sans limite du nombre de lignes, avec leur date, leur variation du temps disponible et leur motif, ainsi que le total consommé automatiquement par motif. La semaine va du lundi 00h00 précédent à ce lundi 00h00, d'après les dates du journal.

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

#### Scenario: Nombreux mouvements manuels
- **GIVEN** 45 ajustements manuels pendant la semaine
- **WHEN** le bilan est fait
- **THEN** le compte rendu liste les 45 mouvements, sans ligne « autre(s) »
