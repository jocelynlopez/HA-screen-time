# Design

## Context

Le rapport du lundi est produit par `render_report` à partir des `Report` que renvoie `Wallet.settle`, puis publié en notification ; rien n'est conservé. `Wallet.settle(now, averages, notes)` modifie le portefeuille et lit la source (`runtime.source.async_fetch`). Les mouvements de la semaine sont déjà extraits par `_week_movements`. L'état est enregistré dans un `Store` avec des clés supplémentaires (`source_entity`, `usage_baselines`). Voir `proposal.md` pour la motivation.

## Goals / Non-Goals

**Goals:**
- Un rapport toujours consultable par l'enfant, dans un format que le tableau de bord affiche tel quel.
- Une prévision exacte du bilan du lundi, sans effet sur l'état réel.

**Non-Goals:**
- Prévoir la consommation à venir, conserver tous les rapports passés, une carte personnalisée.

## Decisions

- **Format** : un capteur « Rapport » dont l'état est la date du dernier bilan (horodatage, ou inconnu s'il n'y en a pas) et dont les attributs contiennent du Markdown. L'état d'un capteur est limité à 255 caractères, d'où les attributs. Les attributs sont exclus de l'historique (`_unrecorded_attributes`) pour ne pas gonfler la base. Le texte déjà produit par `render_report` convient : la carte Markdown de Home Assistant respecte les retours à la ligne. Alternatives écartées : une notification (disparaît), un attribut par vue sur un capteur existant (mélange avec le journal).
- **Historique des rapports** : après chaque bilan, chaque rapport (un par lundi traité, rendu séparément par `render_report([rapport])`) est ajouté à la liste `reports` de l'état (date du lundi, titre, texte), même quand la notification hebdomadaire est désactivée. La liste est bornée aux 52 derniers rapports. `last_report` est le plus récent ; `history` expose les 12 précédents (du plus récent au plus ancien), pour garder les attributs d'une taille raisonnable. La langue est celle de Home Assistant au moment du bilan. La prévision n'est jamais enregistrée.
- **Prévision** : `Wallet.forecast(now, averages, notes)` copie le portefeuille (`to_dict`/`from_dict`, avec la configuration), y exécute `settle` à la date du prochain lundi 00h00 et renvoie le dernier compte rendu ; l'original n'est jamais touché. Comme `settle` rattrape les lundis dus, la prévision reste juste quand un bilan est en retard. Elle reprend `Report.manual` et `Report.automatic`, donc les mouvements de la semaine en cours.
- **Titre de la prévision** : « Prévision du lundi {date} » plus une ligne « Si rien ne change d'ici là ». Le reste utilise le même rendu que le rapport du lundi.
- **Source indisponible** : la prévision lit la source comme un bilan. Si elle échoue, ou s'il n'y a pas de source, la prévision se limite aux mouvements de la semaine et à une ligne « Prévision indisponible : source des notes inaccessible », pour que l'enfant voie quand même le temps donné ou retiré. Aucune notification d'erreur supplémentaire (le bilan réel s'en charge).
- **Mise à jour** : le runtime recalcule la prévision au chargement, après chaque mouvement (`async_notify_entities`), après un bilan et quand l'état du capteur de notes change. Le calcul n'enregistre rien ; il est sérialisé par le verrou du runtime, et un calcul en cours est remplacé par le suivant.
- **Aucune migration** : `reports` est facultative comme `source_entity` ; un état sans cette clé donne un historique vide jusqu'au prochain bilan.

## Risks / Trade-offs

- [Lecture de la source à chaque mouvement] Les consommations automatiques déclenchent un recalcul à chaque relevé → la lecture est locale (état d'un capteur) et le calcul sur quelques notes est négligeable ; un seul calcul à la fois.
- [Taille de l'état] 52 rapports d'environ 2 Ko pèsent une centaine de Ko dans le fichier d'état → acceptable ; seuls 13 rapports sont exposés en attributs, exclus de l'historique de la base.
- [Rapport avant le premier bilan] Juste après l'installation, `last_report` est vide → le capteur affiche « Aucun rapport pour le moment » ; la prévision, elle, est disponible.
- [Prévision et consommation à venir] Le temps disponible prévu ne tient pas compte de ce qui sera consommé d'ici lundi → c'est dit dans le titre (« Si rien ne change d'ici là »).
- [Langue figée] Le dernier rapport garde la langue du bilan → acceptable, un seul rapport par semaine.

## Hypothèses à confirmer

Points que la demande n'a pas tranchés et que les specs écrivent. À valider ou corriger avant l'implémentation :
- Un seul capteur « Rapport » à trois attributs (`last_report`, `history`, `forecast`), plutôt que deux capteurs.
- L'historique des rapports du lundi est conservé (52 au plus, soit un an), un rapport par lundi traité, y compris les lundis rattrapés ; les prévisions ne sont pas conservées.
- Le capteur expose le dernier rapport (`last_report`) et les 12 précédents (`history`).
- La prévision suppose qu'aucune consommation ne s'ajoute d'ici lundi ; ce n'est pas une projection de l'usage.
- La prévision est recalculée à chaque mouvement et à chaque changement du capteur de notes, sans bouton ni action de rafraîchissement.
- La prévision est affichée même si la notification hebdomadaire est désactivée.
- Version mineure `0.7.0`.
