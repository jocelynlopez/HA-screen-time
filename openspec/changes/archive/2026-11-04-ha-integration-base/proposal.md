# Proposal

## Why

La logique du portefeuille (`weekly-credit-model`) est livrée mais isolée : elle ne tourne que dans les tests. Pour qu'elle serve sur Home Assistant, il faut l'emballer dans une intégration personnalisée installable via HACS : paramètres modifiables dans l'interface, état conservé après un redémarrage, bilan automatique chaque lundi, capteurs lisibles dans les tableaux de bord et services appelables par les automatisations. Les sources de données (notes EcoleDirecte, consommation Windows) viennent dans des changes séparés, branchés sur cette base.

## What Changes

- Une **intégration Home Assistant `screen_time_wallet`** dans `custom_components/screen_time_wallet/`, installable par HACS ou par copie. Elle gère **un portefeuille par entrée de configuration** (un enfant par entrée).
- Le cœur Python actuel est **déplacé** dans l'intégration (sous-paquet `engine`), car HACS n'installe que ce dossier. Le projet n'est plus un paquet Python installable.
- **Configuration dans l'interface** : création d'un portefeuille par le nom de l'enfant, puis options modifiables (temps maximal en heures, part des notes en pourcentage, pivot, poids minimal, nombre minimal de matières, crédit de repli, exclusion des notes non significatives, service de notification) et édition de la table des multiplicateurs de matière.
- **Persistance** de l'état (crédit hebdomadaire, capital notes, dernier bilan, notes déjà vues, journal) dans le stockage de HA.
- **Bilan automatique** chaque lundi à 00h00 (heure locale de HA), avec rattrapage au démarrage.
- **Entités** par portefeuille : temps disponible, crédit hebdomadaire, capital notes et dernier bilan (avec le journal des mouvements en attribut).
- **Services** : consommation (crédit hebdomadaire d'abord) et ajustement manuel parental (signé, avec motif).
- **Notifications d'anomalie** : une notification persistante de HA, et en option un service `notify`, quand une matière est inconnue ou qu'une note est rejetée.
- **Rapport hebdomadaire** : chaque lundi, un mini-rapport qui détaille le calcul (moyenne générale, crédit initial, notes de la semaine, moyenne et crédit de semaine, capital et temps disponible), publié comme notification persistante et envoyé au service `notify` configuré. Il se désactive dans les options.
- **Point de branchement** pour la source de moyennes et de notes. Sans source, le bilan utilise le crédit de repli et un crédit de semaine nul.
- **Cœur** : ajout d'un journal des mouvements, de l'ajustement manuel et d'un état sérialisable ; le compte rendu du bilan expose maintenant les éléments du calcul pour alimenter le rapport.
- Traductions françaises et anglaises, métadonnées HACS, tests avec `pytest-homeassistant-custom-component`.

## Capabilities

### New Capabilities
- `ha-integration`: comportement de l'intégration dans Home Assistant : entrées de configuration, options, persistance, bilan automatique, source branchable, entités, services, notifications, traductions et métadonnées d'installation.

### Modified Capabilities
- `screen-time-wallet`: ajout du journal des mouvements, de l'ajustement manuel et de l'état sérialisable ; l'exigence « Compte rendu du bilan » est étendue aux éléments du calcul.

## Impact

- Réorganisation du dépôt : `src/portefeuille_minutes/` devient `custom_components/screen_time_wallet/engine/`, nouveau code d'intégration à côté, `hacs.json` à la racine, `pyproject.toml` simplifié (projet non packagé, Python ≥ 3.14.2).
- Nouvelle dépendance de développement : `pytest-homeassistant-custom-component` (installe `homeassistant==2026.10.4` dans l'environnement de dev). Aucune dépendance à l'exécution dans HA.
- Les 86 tests existants sont conservés et leurs imports adaptés.

## Hors périmètre

- Lecture des capteurs EcoleDirecte (moyennes, notes) : change `ha-grades-source`.
- Mesure de la consommation (Windows, prise connectée, Family Link) : changes suivants.
- Carte de tableau de bord, blueprint d'automatisation, publication HACS officielle.
- Plafond du capital notes.
