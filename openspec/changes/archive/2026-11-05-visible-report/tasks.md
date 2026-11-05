# Tasks

## 1. Cœur

- [x] 1.1 Ajouter `Wallet.forecast(now, averages, notes)` : copie du portefeuille, bilan au prochain lundi 00h00, dernier compte rendu renvoyé, original intact ; vérifier « Prévision du prochain bilan » par des tests marqués (sans effet, notes à venir, mouvements de la semaine, bilan en retard, répétée)

## 2. Intégration

- [x] 2.1 Ajouter au rapport le titre de prévision (« Prévision du lundi {date} », « Si rien ne change d'ici là »), le rendu sans source (mouvements de la semaine et mention d'indisponibilité) et « Aucun rapport pour le moment », textes fr et en
- [x] 2.2 Dans `runtime.py`, enregistrer chaque rapport du lundi dans la liste facultative `reports` (52 au plus) après chaque bilan, indépendamment de la notification, et la charger dans `__init__.py` ; vérifier « Historique des rapports » par des tests marqués (redémarrage, lundis rattrapés, limite de 52, ancien état, prévision non enregistrée)
- [x] 2.3 Dans `runtime.py`, calculer la prévision au chargement, après chaque mouvement ou bilan et à chaque changement du capteur de notes, sans notification d'erreur ni enregistrement ; vérifier « Prévision du rapport » par des tests marqués (mouvement, capteur de notes, source inaccessible, état inchangé)
- [x] 2.4 Ajouter le capteur « Rapport » dans `sensor.py` (état = date du bilan, attributs `last_report`, `history` et `forecast`, `_unrecorded_attributes`) avec traductions fr et en ; vérifier « Capteur Rapport » par des tests marqués (attributs, avant le premier bilan, sans notification) et que les tests de traductions passent

## 3. Documentation

- [x] 3.1 Mettre à jour le `README.md` anglais et français : capteur « Rapport » et exemple de carte Markdown (`last_report`, `history` et `forecast`)

## 4. Intégration

- [x] 4.1 Lancer `uv run pytest` et vérifier que tous les tests passent, y compris le test de couverture des exigences
- [x] 4.2 Relire les « Hypothèses à confirmer » de `design.md` et vérifier que chacune est confirmée par l'utilisateur ou corrigée dans les specs avant l'archivage
- [x] 4.3 À l'archivage, vérifier que `openspec validate --specs --strict` passe

## Workflow follow-up

- Publier la version mineure `0.7.0` (version du `manifest.json` et tag `v0.7.0`) après l'archivage.
- Ajouter la carte Markdown au tableau de bord de l'enfant et vérifier que les retours à la ligne s'affichent.
