# Design

## Context

Le cœur Python (`config`, `grades`, `credit`, `wallet`) est pur : pas d'I/O, dates injectées, 86 tests. Il vit aujourd'hui dans `src/portefeuille_minutes/`. HACS n'installe que `custom_components/<domaine>/` : le cœur doit donc vivre dans ce dossier. Home Assistant exécute Python ≥ 3.14.2 dans sa version actuelle (2026.10.x), ce que le projet utilise déjà. Voir `proposal.md` pour la motivation et les specs `ha-integration` et `screen-time-wallet` pour le comportement.

## Goals / Non-Goals

**Goals:**
- Une intégration installable par HACS ou par copie dans `config/custom_components/`, sans dépendance à l'exécution.
- Tout paramètre du cœur modifiable dans l'interface, sans redémarrage.
- L'état survit à un redémarrage ; les bilans manqués sont rattrapés.
- Chaque exigence testée avec une instance HA de test.

**Non-Goals:**
- Lecture des capteurs EcoleDirecte et mesure de la consommation (changes suivants).
- Carte, blueprint, publication HACS officielle.

## Decisions

- **Disposition du dépôt** : `custom_components/screen_time_wallet/` contient l'intégration et, dans `engine/`, le cœur déplacé tel quel. Le projet cesse d'être un paquet installable (`[tool.uv] package = false`, plus de `[build-system]` ni de script). Alternatives écartées : garder `src/` et copier à la publication (deux sources de vérité) ; publier le cœur sur PyPI (démarche disproportionnée pour un usage familial).
- **Un objet d'exécution par entrée** (`WalletRuntime`) : détient le `Wallet`, le stockage, la source et un verrou `asyncio` qui sérialise bilan, consommation et ajustement. Les entités se rafraîchissent par un signal `dispatcher` propre à l'entrée, après chaque modification suivie d'un enregistrement.
- **Stockage HA (`Store`)**, une clé par entrée, enregistré après chaque changement : l'état est petit. Les clés de notes (tuples contenant des `Fraction`) sont sérialisées avec un type explicite pour être restaurées à l'identique.
- **Options plutôt que champs de configuration** : le flux de configuration ne demande que le nom ; tout le reste est dans le flux d'options, à deux étapes (paramètres, table des matières). Une modification recharge l'entrée ; l'état est restauré depuis le stockage, donc rien n'est perdu.
- **Unités de l'interface** : heures et pourcentage dans les formulaires, converties en minutes et en fraction pour le cœur, dans une fonction pure testée à part (`options.py`).
- **Bilan** : un déclencheur quotidien à 00h00 locale (`async_track_time_change`), plus un rattrapage au chargement. Le cœur décide s'il y a un lundi à traiter : le déclencheur n'a aucune logique de jour.
- **Source branchable** : un protocole `GradesSource` (méthode asynchrone qui renvoie moyennes et notes) et une `NullSource` par défaut. Le change `ha-grades-source` fournira l'implémentation EcoleDirecte. Alternative écartée : lire les capteurs EcoleDirecte dès ce change, ce qui mélange deux sujets difficiles à valider séparément.
- **Services d'entité** (`consume`, `adjust`) enregistrés sur la plateforme capteur, déclarés dans `services.yaml` : on cible un capteur du portefeuille. Ils fonctionnent sur les quatre capteurs ; la documentation désigne « Temps disponible ».
- **Notifications** : `persistent_notification` avec un identifiant par entrée (donc mise à jour sans doublon), et appel du service `notify` configuré s'il existe.
- **Rapport hebdomadaire** : texte produit par une fonction pure (`report.py`) à partir du compte rendu du bilan, avec des libellés français et anglais gardés dans `report.py` (la catégorie de traductions de HA ne couvre pas les textes de notification), choisis selon la langue de HA, et dont la parité entre les deux langues est testée. Publié sous un identifiant de notification distinct de celui des anomalies. Le compte rendu du cœur porte les chiffres du calcul, pour que le rapport ne recalcule rien. Alternative écartée : recalculer dans la couche HA, qui dupliquerait les formules.
- **Temps** : `dt_util.now()` converti en date locale naïve, comme attendu par le cœur ; la date du dernier bilan est exposée avec fuseau.
- **Tests** : `pytest-homeassistant-custom-component` (instance HA de test réelle), avec le marqueur `requirement` existant pour la traçabilité.

## Risks / Trade-offs

- [Le plugin de test épingle `homeassistant==2026.10.4`] → la dépendance de développement évolue avec HA ; la version de HA de ta machine doit être compatible, à vérifier à l'installation.
- [Importer le cœur charge le paquet de l'intégration, donc HA] → acceptable : le plugin installe HA en développement, et `__init__.py` reste léger.
- [API de HA changeante] → l'intégration n'utilise que des API stables (config entries, `Store`, capteurs, services d'entité).
- [Aucune source dans ce change] → le portefeuille donne 240 min de repli chaque lundi tant que `ha-grades-source` n'est pas livré.
- [Vérification réelle impossible ici] → je teste avec une instance HA de test, mais l'installation sur ton HA Container reste à valider par toi.

## Hypothèses à confirmer

Points que les échanges n'ont pas tranchés et que les specs écrivent. À valider ou corriger avant l'implémentation :
- Le cœur est déplacé dans l'intégration et le projet n'est plus packagé ; `requires-python` passe à ≥ 3.14.2.
- Sans source, le bilan applique le crédit de repli (240 min) et un crédit de semaine nul.
- Si la source échoue, le bilan est reporté au déclenchement suivant, sans notification.
- Les services ciblent un capteur du portefeuille et fonctionnent sur les quatre ; le journal conserve 200 mouvements dont 20 sont exposés.
- Le service de notification se saisit comme une chaîne (par exemple `notify.mobile_app_telephone`).
- Heure locale de HA pour le lundi 00h00, sans prise en charge du changement d'heure au-delà de ce que fait `dt_util`.
- La version de l'intégration démarre à 0.1.0, avec le mode de connexion `calculated`.
- Le rapport hebdomadaire est activé par défaut, publié à chaque bilan (même sans note), et un seul message regroupe les lundis rattrapés ; il est distinct de la notification d'anomalie.
