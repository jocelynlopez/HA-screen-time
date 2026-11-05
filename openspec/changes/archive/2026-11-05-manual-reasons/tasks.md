# Tasks

## 1. Cœur

- [x] 1.1 Marquer l'origine automatique des consommations (`detail["origin"] = "auto"` à la création) et limiter le regroupement aux mouvements automatiques ; vérifier « Origine des mouvements » par des tests marqués (marquée, manuelle sans origine, ajustement sans origine, automatique après manuelle de même motif) et que les tests de regroupement existants passent
- [x] 1.2 Ajouter à `Report` les mouvements manuels et les totaux automatiques de la semaine (par date, entre le lundi précédent et ce lundi) ; vérifier « Mouvements de la semaine dans le compte rendu » par des tests marqués (mouvements manuels, total par capteur, semaine sans mouvement, autre semaine, plusieurs lundis rattrapés)

## 2. Intégration

- [x] 2.1 Retirer `number.py`, `button.py`, `control_minutes`, les constantes, les textes de traduction et le motif « bouton », les plateformes `number` et `button` de `PLATFORMS` et le test `tests/ha/test_controls.py` ; supprimer du registre, au chargement de l'entrée, les entités `number` « minutes » et `button` « add_time » et « remove_time » d'après leur identifiant unique ; vérifier « Entités de commande retirées » par des tests marqués (entités orphelines supprimées, capteurs conservés) et que tous les autres tests passent
- [x] 2.2 Ajouter au rapport hebdomadaire la section « Mouvements manuels de la semaine » (date, minutes signées, motif ou « sans motif », une ligne par capteur automatique, limite de 30 lignes, sections vides omises), textes fr et en ; vérifier « Mouvements manuels dans le rapport » par des tests marqués (avec mouvements, sans motif, consommation automatique, aucun mouvement)
- [x] 2.3 Ajouter `blueprints/script/screen_time_wallet/add_time.yaml` et `remove_time.yaml` (capteur du portefeuille, minutes de 1 à 600, raison obligatoire, appel de `adjust` ou `consume`) ; vérifier « Blueprints de script » par des tests marqués qui chargent les YAML (champs, bornes, action appelée, lien d'import du README)

## 3. Documentation

- [x] 3.1 Mettre à jour le `README.md` anglais et français : liens d'import des blueprints, création du script, repli à copier à la main, section du rapport hebdomadaire, retrait de l'entité « Minutes » et des boutons ; vérifier que les tests du README et des traductions passent

## 4. Intégration

- [x] 4.1 Lancer `uv run pytest` et vérifier que tous les tests passent, y compris le test de couverture des exigences
- [x] 4.2 Relire les « Hypothèses à confirmer » de `design.md` et vérifier que chacune est confirmée par l'utilisateur ou corrigée dans les specs avant l'archivage
- [x] 4.3 À l'archivage, vérifier que `openspec validate --specs --strict` passe

## Workflow follow-up

- Publier la version mineure `0.6.0` (version du `manifest.json` et tag `v0.6.0`) après l'archivage : le retrait des entités n'est pas rétrocompatible.
- Importer les blueprints sur l'installation réelle et vérifier que la fenêtre de saisie s'affiche, puis qu'une raison saisie apparaît dans le rapport du lundi suivant.
