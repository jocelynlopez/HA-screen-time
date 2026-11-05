# Tasks

## 1. Cœur

- [x] 1.1 Dans `Wallet.activate_source`, ne mémoriser que les notes datées d'avant le lundi 00h00 de la semaine en cours (date illisible = ancienne) ; adapter les tests d'activation existants dont les notes sont datées de la semaine en cours ; vérifier « Activation d'une source » par des tests marqués (notes de la semaine en cours conservées, note précédente mémorisée) et que les scénarios existants passent
- [x] 1.2 Ajouter `Wallet.recount_week(now, notes)` qui retire des notes vues celles de la semaine en cours et renvoie leur nombre, sans toucher aux crédits ni au journal ; vérifier « Recomptage des notes de la semaine » par des tests marqués (notes rendues à compter, notes précédentes, aucune note, crédits et journal)

## 2. Intégration

- [x] 2.1 Ajouter `WalletRuntime.async_recount_week` (lecture de la source, recomptage sous le verrou, enregistrement, prévision rafraîchie, `ServiceValidationError` si la source échoue), l'action d'entité `recount_week` dans `sensor.py` (schéma vide), `services.yaml` et les traductions fr et en ; vérifier « Action de recomptage des notes » et « Activation de la source » (notes de la semaine à l'activation) par des tests marqués (recomptage, source inaccessible, aucune note, crédits et journal) et que les tests de traductions et du README passent

## 3. Documentation

- [x] 3.1 Mettre à jour le `README.md` anglais et français : l'action `recount_week`, quand l'utiliser (après une activation en cours de semaine) et son avertissement (ne pas l'utiliser après un bilan tardif)

## 4. Intégration

- [x] 4.1 Lancer `uv run pytest` et vérifier que tous les tests passent, y compris le test de couverture des exigences
- [x] 4.2 Relire les « Hypothèses à confirmer » de `design.md` et vérifier que chacune est confirmée par l'utilisateur ou corrigée dans les specs avant l'archivage
- [x] 4.3 À l'archivage, vérifier que `openspec validate --specs --strict` passe

## Workflow follow-up

- Publier la version mineure `0.9.0` (version du `manifest.json` et tag `v0.9.0`) après l'archivage.
- Lancer l'action `screen_time_wallet.recount_week` une fois sur le portefeuille de Mael et vérifier que la prévision affiche le français du 02/11 et les arts plastiques du 03/11.
