# Spec Delta

## MODIFIED Requirements

### Requirement: Rapport hebdomadaire
Le système SHALL, à l'issue de chaque bilan et si l'option est activée, publier un rapport simple pour l'enfant : le titre « Ton temps de la semaine (lundi JJ/MM) », le temps reporté des semaines précédentes (s'il est non nul), chaque note comptée avec ses minutes signées, le complément de la moyenne générale avec la moyenne entre parenthèses, puis le temps disponible. Le détail technique du calcul n'y figure pas. Notification persistante distincte de celle des anomalies, envoyée aussi au service configuré.

#### Scenario: Contenu du rapport
- **GIVEN** un bilan avec sept moyennes, un capital de 0 et les notes arts plastiques 9/10 et français 7/20
- **WHEN** le rapport est publié
- **THEN** il indique la date du lundi, les deux notes comptées avec +42 et −415 minutes, un complément de la moyenne générale (15,80) de +227 minutes et un temps disponible de −146 minutes, sans crédit initial ni poids

#### Scenario: Semaine sans note
- **WHEN** aucune note n'a été vue pendant la semaine
- **THEN** le rapport n'a aucune ligne de note et son complément de la moyenne générale contient tout le crédit du lundi

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

#### Scenario: Temps reporté
- **GIVEN** un capital notes de 145 minutes avant le bilan
- **WHEN** le rapport est publié
- **THEN** il indique « Reporté des semaines précédentes » avec +145 minutes ; avec un capital nul, cette ligne est absente
