# Tasks

## 1. Cœur

- [x] 1.1 Calculer dans `week_details` les minutes apportées par chaque note comptée (arrondies, notes non significatives ignorées selon l'option) ; dans `Wallet.settle`, noter le capital avant le bilan ; ajouter à `Report` `note_minutes`, `carried` et `complement` (reste : crédit initial + crédit de semaine − somme des minutes des notes), vides en semaine de repli ; vérifier « Minutes apportées par chaque note » par des tests marqués (minutes de chaque note, somme exacte, capital reporté, semaine sans note, semaine partielle, repli, note non significative) et que les tests de crédits existants passent

## 2. Intégration

- [x] 2.1 Réécrire `_report_lines` et les textes fr et en : bloc « Ton temps de la semaine (lundi JJ/MM) », reporté (si non nul), une ligne par note avec ses minutes, « Complément moyenne générale (moyenne) », « Temps disponible » ; supprimer les anciens textes du détail technique, garder l'affichage de la semaine de repli et les sections de mouvements ; adapter les tests existants du contenu du rapport (`tests/ha/test_settlement.py`, `tests/ha/test_report_sensor.py`, `tests/test_report_movements.py`) ; vérifier « Rapport hebdomadaire » par des tests marqués (contenu, semaine sans note, repli, temps reporté, lundis manqués) et la prévision

## 3. Documentation

- [x] 3.1 Mettre à jour le `README.md` anglais et français : exemple de rapport avec les minutes par note, le temps reporté et le complément ; retirer la description du détail technique

## 4. Intégration

- [x] 4.1 Lancer `uv run pytest` et vérifier que tous les tests passent, y compris le test de couverture des exigences
- [x] 4.2 Relire les « Hypothèses à confirmer » de `design.md` et vérifier que chacune est confirmée par l'utilisateur ou corrigée dans les specs avant l'archivage
- [x] 4.3 À l'archivage, vérifier que `openspec validate --specs --strict` passe

## Workflow follow-up

- Publier la version mineure `0.8.0` (version du `manifest.json` et tag `v0.8.0`) après l'archivage.
- Attendre une note (ou en ajouter une dans la source de test) pour vérifier sur la prévision que les minutes par note s'affichent comme prévu.
