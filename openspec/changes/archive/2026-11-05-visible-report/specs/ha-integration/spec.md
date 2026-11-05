# Spec Delta

## ADDED Requirements

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
