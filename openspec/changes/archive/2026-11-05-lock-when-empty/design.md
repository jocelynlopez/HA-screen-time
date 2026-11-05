# Design

## Context

Le temps disponible (`Wallet.available`) change à chaque consommation, ajustement et bilan ; le runtime appelle `async_notify_entities()` après chacun de ces changements et `async_sync_usage()` à chaque relevé des capteurs de temps d'écran. L'intégration `microsoft_family_safety` expose l'Account Lock `switch.<prénom>_lock` : ON met le temps autorisé à 0 pour tous les jours (toutes les plateformes), OFF restaure les quotas enregistrés ; l'écriture prend environ une minute et l'API est non officielle. Voir `proposal.md` pour la motivation et la spec `ha-integration` pour le comportement.

## Goals / Non-Goals

**Goals:**
- Que le blocage suive le temps disponible sans automatisation de l'utilisateur.
- Un état qui converge : un basculement manquant, échoué ou annulé à la main est corrigé au relevé suivant.

**Non-Goals:**
- Avertir avant la coupure, piloter autre chose que des `switch`, contourner le délai de l'API Microsoft.

## Decisions

- **Deux listes pour deux sens** (`lock_switches` : ON = bloqué ; `allow_switches` : OFF = bloqué) plutôt qu'un sens par interrupteur : pas d'écran de réglage supplémentaire, et le sens est visible dans les options. Alternative écartée : une liste unique avec un sens par entrée, qui demanderait un formulaire dédié.
- **État voulu, pas événements** : le runtime calcule un état voulu (`bloqué` quand `available <= 0`) et le compare à l'état réel de chaque interrupteur ; il n'appelle `switch.turn_on` ou `switch.turn_off` que s'il diffère. Cette approche rend les nouvelles tentatives, le démarrage et l'annulation d'un basculement manuel identiques à l'usage normal. Alternative écartée : basculer au passage du seuil, qui n'est pas réessayé en cas d'échec.
- **Points d'application** : à la fin de `async_sync_usage()` (chaque relevé, même sans consommation), de `async_refresh()` (démarrage, bilan) et après chaque modification du portefeuille (`async_notify_entities`). Un relevé identique au précédent ne change pas l'état du capteur : il est capté par l'événement « état rapporté » de Home Assistant, de sorte que l'état des interrupteurs est imposé à chaque relevé, même sans consommation. Aucun appel tant que `pending_settlements() > 0`, comme pour la consommation, pour ne pas bloquer l'enfant sur un crédit périmé.
- **Hors du verrou et en tâche de fond** : le basculement d'un interrupteur peut durer une minute (Family Safety) ; il est lancé comme tâche de fond, sérialisée par un verrou propre, et relit `available` à l'exécution. Il n'attend jamais le verrou du portefeuille. Alternative écartée : l'attendre dans le verrou, qui bloquerait les relevés et les services.
- **Appel des services** `switch.turn_on` / `switch.turn_off` avec `blocking=True` pour détecter l'échec ; une exception est journalisée et signalée par la notification persistante (identifiant propre), supprimée au succès. Un interrupteur « unavailable » ou « unknown » est ignoré sans notification : il est réessayé au relevé suivant.
- **Seuil** : `available <= 0` bloque, `available > 0` libère.
- **Options** : deux sélecteurs d'entités multiples limités au domaine `switch`, champ vidé = liste vide, entité inexistante refusée (comme les capteurs de temps d'écran).

## Risks / Trade-offs

- [Retard du blocage] Le capteur de temps d'écran est relevé toutes les 5 minutes puis l'écriture Microsoft prend environ une minute → le blocage peut avoir jusqu'à plusieurs minutes de retard, et le temps d'écran peut devenir négatif ; c'est tracé dans le capital notes.
- [Verrou de tout le compte] L'Account Lock touche toutes les plateformes (Windows, Xbox, téléphone) → accepté par l'utilisateur.
- [Ajout d'un interrupteur avec un temps déjà épuisé] L'enfant est bloqué dès l'enregistrement des options → c'est le comportement voulu, mais à documenter.
- [Interrupteur déverrouillé à la main sans crédit] Il est reverrouillé au relevé suivant ; pour donner du temps, on utilise l'ajustement → documenté dans le README.
- [API non officielle] Un échec persistant laisse l'enfant dans l'état précédent → la notification d'échec le signale, et l'utilisateur peut vider les listes pour reprendre la main.

## Hypothèses à confirmer

Points que la demande n'a pas tranchés et que les specs écrivent. À valider ou corriger avant l'implémentation :
- Deux listes d'interrupteurs : verrouillage (ON = bloqué) et autorisation (OFF = bloqué).
- Le temps disponible inférieur ou égal à 0 bloque ; strictement positif libère.
- L'état est remis en accord à chaque relevé, au démarrage et après un bilan, une consommation ou un ajustement ; un basculement manuel contraire est annulé.
- Aucun changement tant qu'un bilan du lundi est dû.
- Un échec de basculement est signalé par une notification persistante, réessayé au relevé suivant ; un interrupteur indisponible est ignoré sans notification.
- Seules les entités du domaine `switch` sont acceptées.
- Aucun avertissement avant la coupure (hors périmètre).
