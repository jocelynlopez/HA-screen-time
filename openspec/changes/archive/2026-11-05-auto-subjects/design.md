# Design

## Context

La table des multiplicateurs est une option (`multipliers`, nom → multiplicateur) convertie en `Config` pour le cœur. Dans le cœur, une matière absente de la table a le multiplicateur 0 : ses moyennes et ses notes sont ignorées et la matière est signalée dans le compte rendu (`unknown_subjects`). `EcoleDirecteSource.async_fetch` renvoie les moyennes des capteurs de matière (attributs `Nom` et `Code`, seulement quand la moyenne est numérique) et les notes ; le runtime les lit à l'activation de la source (`async_activate`) et avant chaque bilan (`_async_settle`). Les options sont aujourd'hui modifiées seulement par les flux de configuration, et tout changement d'options recharge l'entrée (`_async_options_updated`). Voir `proposal.md` pour la motivation et la spec `ha-integration` pour le comportement.

## Goals / Non-Goals

**Goals:**
- Qu'une matière publiée par la source compte dès le calcul en cours, avec le multiplicateur 1, sans saisie.
- Que la matière ajoutée soit visible et modifiable comme toute autre dans les options.

**Non-Goals:**
- Changer le cœur, détecter en continu, lister la table dans l'interface, retirer les matières disparues.

## Decisions

- **Détection dans la couche Home Assistant, cœur inchangé** : le cœur garde « absente de la table = 0 » (spec `grade-conversion`). Le runtime ajoute les matières à la table avant d'appeler le cœur, si bien que l'état « inconnue » n'atteint plus un bilan. Alternative écartée : un multiplicateur par défaut de 1 dans le cœur, qui n'écrirait nulle part la matière et empêcherait de la voir ou de la régler.
- **Matières lues dans la source** (`SourceData.subjects`) : noms des capteurs de matière, avec ou sans moyenne, puis matières des notes. Une matière sans moyenne est donc ajoutée avant sa première moyenne. Les doublons (casse, accents, ponctuation) sont écartés avec `normalize_subject` ; le premier nom rencontré est conservé.
- **Moment** : à l'activation de la source, avant le calcul du crédit initial, et avant chaque bilan, sous le verrou, juste après la lecture de la source. Une matière qui apparaît en cours de semaine est ajoutée au bilan suivant, ce qui suffit puisque ses effets ne se calculent qu'à ce moment.
- **Écriture dans les options sans rechargement** : le runtime reconstruit sa `Config` en mémoire (`build_config`) pour le calcul en cours, puis enregistre la nouvelle table avec `async_update_entry`. L'écouteur d'options recharge d'ordinaire l'entrée, ce qui interromprait le bilan et dédoublerait les lectures ; un drapeau du runtime lui indique de ne pas recharger pour cette mise à jour. Alternative écartée : laisser recharger, au risque de perdre le fil du bilan en cours.
- **Une matière à 0 ou modifiée n'est jamais touchée** : seule l'absence de la table déclenche un ajout.
- **Suppression** : une matière supprimée qui est encore dans la source est rajoutée avec 1 à la détection suivante ; pour l'exclure, on lui donne 0. Alternative écartée : mémoriser les suppressions, ce qui ajouterait un état à gérer pour un cas rare.
- **Notification à l'ajout** : une notification persistante propre au portefeuille (identifiant `..._subjects`), mise à jour sans doublon, nomme les matières ajoutées et renvoie vers *Configurer → Matières et multiplicateurs* ; le service de notification configuré reçoit le même message (réutilise la publication existante).
- **Détection à la demande** : la case « Détecter les matières de la source » de l'écran *Matières* appelle la même fonction de détection que l'automatique, via le runtime de l'entrée, sans recharger l'entrée. Le champ matière n'est obligatoire que si la case est décochée. L'écran se termine par un message de résultat (matières ajoutées, aucune, source indisponible, aucune source choisie), sans notification persistante : l'utilisateur voit le résultat. Alternative écartée : une entité *button* ou un service, plus éloignés de l'endroit où l'on règle les matières.
- **Notification d'anomalie** : elle ne signale plus que les notes rejetées. Le champ `unknown_subjects` du compte rendu du cœur reste, il n'est simplement plus affiché.

## Risks / Trade-offs

- [Matières non scolaires ajoutées avec 1] Les capteurs publient aussi des rubriques comme « VIE DE CLASSE » ; si elles ont une moyenne, elles entrent dans la moyenne générale avec le poids 1 → la notification les nomme pour que l'utilisateur mette 0 sur celles à exclure.
- [Crédit modifié par l'ajout] L'arrivée d'une matière change la moyenne générale et donc le crédit hebdomadaire du bilan en cours → voulu, la matière est alors comptée comme les autres ; la notification précède le rapport.
- [Mise à jour des options pendant une modification par l'utilisateur] Une saisie simultanée dans les options pourrait écraser l'ajout → les ajouts sont refaits à la détection suivante.
- [Option modifiée en dehors de l'interface] Un fichier d'options sans table est complété par la table par défaut avant l'ajout.

## Hypothèses à confirmer

Points que la demande n'a pas tranchés et que les specs écrivent. À valider ou corriger avant l'implémentation :
- La détection a lieu à l'activation de la source et avant chaque bilan, pas à chaque changement de capteur.
- Les matières d'un capteur sans moyenne numérique et celles qui ne figurent que dans les notes sont ajoutées aussi.
- Le nom conservé est celui de la source, comparé sans tenir compte de la casse, des accents ni de la ponctuation.
- Une matière supprimée mais encore publiée par la source est rajoutée avec 1 ; le multiplicateur 0 est le moyen de l'exclure.
- Une matière déjà présente à 0 n'est pas modifiée.
- La détection à la demande n'envoie pas de notification persistante et ne recalcule pas le crédit en cours : les matières comptent à partir du prochain bilan.
- La détection à la demande n'est possible que si une source de notes est choisie et disponible.
- La notification d'anomalie ne signale plus les matières inconnues, seulement les notes rejetées.
