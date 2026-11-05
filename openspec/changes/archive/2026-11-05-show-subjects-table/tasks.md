# Tasks

## 1. Mise en forme

- [x] 1.1 Ajouter `render_subjects_table(table, language)` à `report.py` (ligne Markdown par matière, tri sans casse ni accents, nombres sans zéro superflu, virgule en français) ; vérifier « Table des matières visible » (écran, écriture des nombres) par des tests marqués sur la fonction pure

## 2. Interface

- [x] 2.1 Afficher la table dans le pas *Matières* (placeholder `{table}` dans le texte d'aide, mis à jour après chaque modification) et dans les messages de fin de la détection à la demande, avec leurs traductions fr et en ; vérifier « Table des matières visible » (écran des matières, table mise à jour, détection avec ajout, aucune nouvelle matière) par des tests marqués
- [x] 2.2 Ajouter la table au texte de la notification des matières ajoutées automatiquement et au message du service de notification ; vérifier « Table des matières visible » (notification d'ajout) par un test marqué et mettre à jour les tests existants de la notification d'ajout

## 3. Documentation

- [x] 3.1 Mettre à jour le `README.md` anglais et français : où voir la table des matières ; vérifier que le test du README passe

## 4. Intégration

- [x] 4.1 Lancer `uv run pytest` et vérifier que tous les tests passent, y compris le test de couverture des exigences
- [x] 4.2 Relire les « Hypothèses à confirmer » de `design.md` et vérifier que chacune est confirmée par l'utilisateur ou corrigée dans les specs avant l'archivage
- [x] 4.3 À l'archivage, vérifier que `openspec validate --specs --strict` passe

## Workflow follow-up

- Publier une version mineure (version du `manifest.json` et tag `vX.Y.Z`) après l'archivage.
- Vérifier sur l'installation réelle que la table s'affiche dans l'écran *Matières* et après la détection.
