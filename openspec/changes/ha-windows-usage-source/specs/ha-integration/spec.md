# Spec Delta

## ADDED Requirements

### Requirement: Capteurs de temps d'écran
Le système SHALL permettre de choisir dans les options un ou plusieurs capteurs de temps d'écran, dont l'état est le nombre de minutes utilisées dans la journée. Une entité inexistante SHALL être refusée. L'ajout d'un capteur SHALL prendre son relevé actuel pour référence, et le retrait SHALL oublier sa référence. Par défaut, aucun capteur n'est choisi.

#### Scenario: Choix d'un capteur
- **WHEN** le capteur `sensor.pc_mael_screen_time` est choisi dans les options
- **THEN** le portefeuille le suit et prend son relevé actuel pour référence, sans rien consommer

#### Scenario: Entité inexistante
- **WHEN** une entité qui n'existe pas est saisie
- **THEN** le formulaire est refusé avec un message d'erreur

#### Scenario: Aucun capteur par défaut
- **WHEN** aucun capteur n'est choisi
- **THEN** aucune consommation automatique n'a lieu

#### Scenario: Capteur retiré puis rajouté
- **WHEN** un capteur est retiré des options puis rajouté plus tard
- **THEN** son relevé du moment est une nouvelle référence

### Requirement: Consommation automatique
Le système SHALL consommer automatiquement, à chaque nouveau relevé d'un capteur de temps d'écran choisi, la consommation calculée depuis son relevé de référence, avec pour motif le nom du capteur. Les consommations de plusieurs capteurs s'additionnent. L'état SHALL être enregistré et les entités mises à jour après chaque consommation.

#### Scenario: Consommation d'un relevé
- **GIVEN** un capteur à 10 minutes pris pour référence et un crédit hebdomadaire de 228
- **WHEN** le capteur passe à 25 minutes
- **THEN** le crédit hebdomadaire vaut 213, les capteurs du portefeuille sont mis à jour et le journal mentionne le capteur

#### Scenario: Deux capteurs
- **GIVEN** deux capteurs de temps d'écran
- **WHEN** le premier augmente de 15 minutes et le second de 20
- **THEN** 35 minutes sont consommées au total

#### Scenario: Relevé indisponible
- **WHEN** le capteur passe à « unavailable »
- **THEN** rien n'est consommé et la référence est conservée

#### Scenario: Remise à zéro du compteur
- **GIVEN** une référence de 190 minutes
- **WHEN** le capteur passe à 12 minutes
- **THEN** 12 minutes sont consommées

#### Scenario: Usage supérieur au crédit
- **GIVEN** un crédit hebdomadaire de 10 minutes et un capital notes de 0
- **WHEN** 25 minutes sont consommées automatiquement
- **THEN** le crédit hebdomadaire vaut 0 et le capital notes −15

### Requirement: Relevés de référence conservés
Le système SHALL enregistrer les relevés de référence avec l'état du portefeuille et les restaurer au démarrage, puis relever chaque capteur au démarrage pour consommer la différence survenue pendant l'arrêt. Un rechargement dû à une modification d'options SHALL ne pas refaire les références des capteurs inchangés.

#### Scenario: Redémarrage
- **GIVEN** une référence enregistrée de 25 minutes
- **WHEN** Home Assistant redémarre et que le capteur affiche 40 minutes
- **THEN** 15 minutes sont consommées

#### Scenario: Remise à zéro pendant l'arrêt
- **GIVEN** une référence enregistrée de 190 minutes
- **WHEN** Home Assistant redémarre et que le capteur affiche 12 minutes
- **THEN** 12 minutes sont consommées

#### Scenario: Rechargement par les options
- **WHEN** une autre option est modifiée alors qu'un capteur de temps d'écran est suivi
- **THEN** sa référence est conservée et aucune minute n'est consommée deux fois
