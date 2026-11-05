# Tasks

## 1. Options

- [x] 1.1 Ajouter les options `lock_switches` et `allow_switches` (listes vides par défaut) : sélecteurs d'entités multiples du domaine `switch`, validation contre le registre, champ vidé = liste vide, traductions fr et en ; vérifier « Interrupteurs de blocage » par des tests marqués (verrouillage, autorisation, entité inexistante, aucun par défaut)

## 2. Blocage

- [x] 2.1 Ajouter au runtime le calcul de l'état voulu et son application : appel de `switch.turn_on` ou `switch.turn_off` seulement si l'état diffère, sens inverse pour les interrupteurs d'autorisation, interrupteurs indisponibles ignorés, aucun changement tant qu'un bilan est dû, tâche de fond sérialisée par un verrou propre ; vérifier « Blocage automatique » (temps épuisé, interrupteur d'autorisation, temps rendu, recharge du lundi, plusieurs interrupteurs, déjà dans l'état voulu, indisponible, bilan dû) par des tests marqués
- [x] 2.2 Appeler l'application de l'état après chaque relevé (même sans consommation), au démarrage, après un bilan, une consommation et un ajustement ; vérifier « Blocage automatique » (déblocage manuel annulé au relevé suivant) par un test marqué
- [x] 2.3 Signaler un échec de basculement par une notification persistante propre (textes fr et en), réessayée au relevé suivant et supprimée au succès ; vérifier « Échec du blocage signalé » par des tests marqués

## 3. Documentation

- [x] 3.1 Mettre à jour le `README.md` anglais et français : les deux listes d'interrupteurs, l'exemple Family Safety (`switch.<prénom>_lock` en verrouillage), l'état imposé à chaque relevé, le retard possible, la marche à suivre pour donner du temps (ajustement) ; vérifier que le test du README passe

## 4. Intégration

- [x] 4.1 Lancer `uv run pytest` et vérifier que tous les tests passent, y compris le test de couverture des exigences
- [x] 4.2 Relire les « Hypothèses à confirmer » de `design.md` et vérifier que chacune est confirmée par l'utilisateur ou corrigée dans les specs avant l'archivage
- [x] 4.3 À l'archivage, vérifier que `openspec validate --specs --strict` passe

## Workflow follow-up

- Publier une version mineure (version du `manifest.json` et tag `vX.Y.Z`) après l'archivage.
- Tester sur l'installation réelle avec `switch.<prénom>_lock` : épuiser le temps, observer le blocage (environ une minute), ajouter du temps avec `screen_time_wallet.adjust` et observer le déblocage.
