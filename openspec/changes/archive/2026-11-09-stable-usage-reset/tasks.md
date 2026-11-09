# Tasks

## 1. Cœur

- [x] 1.1 Ajouter `Baseline.suspect` (sérialisé seulement s'il est vrai, absent = faux) et réécrire `consumed_since` selon design.md ; adapter `test_baisse_le_meme_jour_vaut_remise_a_zero` ; vérifier « Remise à zéro du compteur » par des tests marqués (relevé périmé à minuit, remise à zéro après relevé périmé, baisse passagère 46→36→46, baisse confirmée, baisse sans date, sérialisation avec et sans `suspect`)
- [x] 1.2 Supprimer `MAX_MANUAL_LINES` et la ligne « autre(s) » dans `report.py` ; vérifier « Mouvements de la semaine dans le compte rendu » par un test marqué (45 mouvements tous listés)

## 2. Intégration

- [x] 2.1 Test de non-régression de bout en bout (couche Home Assistant) rejouant les relevés de Mael : minuit avec total périmé et baisse passagère le samedi ; le temps disponible ne doit perdre que la consommation réelle ; adapter les tests de `test_usage_wiring.py` si besoin

## 3. Intégration

- [x] 3.1 Lancer `uv run pytest` et vérifier que tous les tests passent, y compris le test de couverture des exigences
- [x] 3.2 Relire les « Hypothèses à confirmer » de `design.md` et vérifier que chacune est confirmée par l'utilisateur ou corrigée dans les specs avant l'archivage
- [x] 3.3 À l'archivage, vérifier que `openspec validate --specs --strict` passe

## Workflow follow-up

- Publier la version patch `0.9.1` (version du `manifest.json` et tag `v0.9.1`) après l'archivage.
- Rendre 77 minutes à Mael avec `screen_time_wallet.adjust` (+77, motif « correction décompte »).
