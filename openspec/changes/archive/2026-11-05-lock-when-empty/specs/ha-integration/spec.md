# Spec Delta

## ADDED Requirements

### Requirement: Interrupteurs de blocage
Le système SHALL permettre de choisir dans les options deux listes d'interrupteurs : des interrupteurs de verrouillage, bloqués à l'état ON, et des interrupteurs d'autorisation, bloqués à l'état OFF. Une entité inexistante SHALL être refusée. Par défaut, les deux listes sont vides et rien n'est piloté.

#### Scenario: Choix d'un interrupteur de verrouillage
- **WHEN** `switch.mael_lock` est choisi comme interrupteur de verrouillage
- **THEN** le portefeuille le pilote

#### Scenario: Choix d'un interrupteur d'autorisation
- **WHEN** `switch.mael_internet` est choisi comme interrupteur d'autorisation
- **THEN** le portefeuille le pilote avec le sens inverse

#### Scenario: Entité inexistante
- **WHEN** une entité qui n'existe pas est saisie
- **THEN** le formulaire est refusé avec un message d'erreur

#### Scenario: Aucun interrupteur par défaut
- **WHEN** les deux listes sont vides
- **THEN** aucun interrupteur n'est piloté et l'utilisateur peut verrouiller à la main

### Requirement: Blocage automatique
Le système SHALL mettre chaque interrupteur choisi à l'état « bloqué » quand le temps disponible est inférieur ou égal à 0 et à l'état « libre » quand il est strictement positif. Il SHALL remettre l'état en accord à chaque relevé d'un capteur de temps d'écran, au démarrage et après un bilan, une consommation ou un ajustement, sans rien changer tant qu'un bilan est dû.

#### Scenario: Temps épuisé
- **GIVEN** un temps disponible de 5 minutes et un interrupteur de verrouillage à OFF
- **WHEN** 5 minutes sont consommées
- **THEN** l'interrupteur passe à ON

#### Scenario: Interrupteur d'autorisation
- **GIVEN** un interrupteur d'autorisation à ON et un temps disponible épuisé
- **WHEN** l'état est remis en accord
- **THEN** l'interrupteur passe à OFF

#### Scenario: Temps rendu
- **GIVEN** un temps épuisé et un interrupteur de verrouillage à ON
- **WHEN** un ajustement de 30 minutes est fait
- **THEN** l'interrupteur repasse à OFF

#### Scenario: Recharge du lundi
- **GIVEN** un temps épuisé et un interrupteur de verrouillage à ON
- **WHEN** le bilan du lundi rend le temps disponible positif
- **THEN** l'interrupteur repasse à OFF

#### Scenario: Déblocage manuel annulé
- **GIVEN** un temps épuisé et un interrupteur de verrouillage remis à OFF à la main
- **WHEN** le capteur de temps d'écran donne un nouveau relevé
- **THEN** l'interrupteur repasse à ON

#### Scenario: Plusieurs interrupteurs
- **GIVEN** un interrupteur de verrouillage et un d'autorisation
- **WHEN** le temps disponible devient nul
- **THEN** le premier passe à ON et le second à OFF

#### Scenario: Interrupteur déjà dans l'état voulu
- **WHEN** l'état voulu est déjà celui de l'interrupteur
- **THEN** aucun service n'est appelé

#### Scenario: Interrupteur indisponible
- **WHEN** un interrupteur est « unavailable » ou « unknown »
- **THEN** rien n'est appelé pour lui et il est réessayé au relevé suivant

#### Scenario: Bilan dû
- **GIVEN** un bilan du lundi dû que la source en panne empêche
- **WHEN** l'état est remis en accord
- **THEN** aucun interrupteur ne change

### Requirement: Échec du blocage signalé
Le système SHALL créer une notification persistante propre au portefeuille quand le basculement d'un interrupteur échoue, en nommant l'interrupteur, la réessayer au prochain relevé et la supprimer dès que le basculement réussit.

#### Scenario: Basculement en échec
- **WHEN** l'appel du service pour `switch.mael_lock` lève une erreur
- **THEN** une notification persistante nomme l'interrupteur et le basculement est réessayé au relevé suivant

#### Scenario: Succès après échec
- **GIVEN** une notification d'échec pour `switch.mael_lock`
- **WHEN** le basculement réussit
- **THEN** la notification est supprimée
