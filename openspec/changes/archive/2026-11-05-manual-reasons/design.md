# Design

## Context

Chaque mouvement du journal est un `Movement(kind, when, weekly_change, capital_change, reason, detail)` ; `detail` (hors comparaison) est enregistré avec l'état et sert déjà aux bilans. Les consommations automatiques arrivent par `Wallet.consume(..., merge=True)` et se regroupent par motif et par jour ; les consommations et ajustements manuels (actions) n'ont qu'un motif libre, facultatif. Le compte rendu d'un bilan (`Report`) et le rapport hebdomadaire (`render_report`) ne contiennent aucun mouvement. Le journal est borné à 200 mouvements. Voir `proposal.md` pour la motivation et les specs `screen-time-wallet` et `ha-integration` pour le comportement.

## Goals / Non-Goals

**Goals:**
- Pouvoir justifier un mouvement manuel depuis le tableau de bord, par une fenêtre de saisie.
- Retrouver, dans le rapport du lundi, ce qui a modifié le solde pendant la semaine.

**Non-Goals:**
- Rendre le motif obligatoire dans les actions, motiver chaque capteur automatique, exporter tout le journal.

## Decisions

- **Origine dans `detail`** : une consommation automatique crée son mouvement avec `detail["origin"] = "auto"` ; le regroupement exige que le dernier mouvement soit automatique, de même motif et du même jour. Les mouvements manuels n'ont pas d'origine. Aucun changement du format enregistré : `detail` existe déjà. Alternative écartée : un champ `origin` du mouvement, qui changerait la version de l'état.
- **Mouvements de la semaine dans le compte rendu** : à la création du compte rendu de chaque lundi, `Wallet` lit son journal entre le lundi précédent (exclu) et ce lundi (inclus) et remplit `Report.manual` (mouvements manuels, ordre chronologique) et `Report.automatic` (total consommé par motif). L'attribution se fait par la date du mouvement, ce qui rattache correctement chaque mouvement quand plusieurs lundis sont rattrapés. Les bilans eux-mêmes n'entrent pas dans la liste.
- **Variation affichée** : la variation du temps disponible, soit `weekly_change + capital_change` (+30 pour un ajustement, −45 pour une consommation).
- **Blueprints de script plutôt que des entités** : une entité ne peut pas ouvrir de fenêtre de saisie, et une intégration ne peut pas créer d'entité `script`. Le dépôt livre donc deux blueprints (`blueprints/script/screen_time_wallet/add_time.yaml` et `remove_time.yaml`) dont le script déclare les champs `minutes` (nombre de 1 à 600) et `raison` (texte obligatoire) ; Home Assistant affiche la fenêtre de saisie au lancement. Chaque blueprint demande le capteur du portefeuille (sélecteur d'entité de l'intégration) et appelle `screen_time_wallet.adjust` ou `screen_time_wallet.consume`. Alternative écartée : conserver l'entité « Motif » avec les boutons, qui impose une saisie préalable puis un appui.
- **Retrait des commandes de la v0.5.0** : `number.py`, `button.py`, `control_minutes`, les constantes, les traductions et le motif par défaut « bouton » sont supprimés. Au démarrage, les entités orphelines (`number` « minutes », `button` « add_time » et « remove_time ») sont retirées du registre d'après leur identifiant unique `{entry_id}_{clé}`, pour ne pas laisser d'entités indisponibles. Le module `entity.py` reste, utilisé par les capteurs.
- **Rapport** : `render_report` ajoute, après les totaux de chaque semaine, la section « Mouvements manuels de la semaine » (une ligne par mouvement : date, minutes signées, motif ou « sans motif ») puis une ligne par capteur automatique ; les sections vides sont omises. La liste est limitée à 30 lignes avec une ligne « … et N autres ».
- **Les actions** `consume` et `adjust` n'ont rien à changer : leur champ `reason` alimente déjà le journal, et les blueprints le remplissent toujours.

## Risks / Trade-offs

- [Mouvements antérieurs à la mise à jour] Les consommations automatiques déjà enregistrées n'ont pas d'origine et seraient listées comme manuelles dans le premier rapport qui les couvre → un seul rapport concerné ; les nouvelles semaines sont justes.
- [Journal borné à 200] Une semaine avec de nombreux mouvements manuels pourrait en chasser les plus anciens avant le bilan → les consommations automatiques sont regroupées par jour, donc 200 mouvements couvrent largement une semaine.
- [Rapport long] Beaucoup de mouvements allongent la notification → limite de 30 lignes, le reste reste dans le journal du capteur « Dernier bilan ».
- [Entités retirées déjà utilisées] Un tableau de bord qui affichait l'entité « Minutes » ou les boutons les montrera indisponibles → changement non rétrocompatible assumé, signalé dans le README et par une version mineure.
- [Blueprint de script avec champs] Je n'ai pas vérifié qu'un blueprint de script accepte des `fields` dans toutes les versions de Home Assistant → un test charge le YAML, et le README donne en repli le script à copier à la main, qui fonctionne.

## Hypothèses à confirmer

Points que la demande n'a pas tranchés et que les specs écrivent. À valider ou corriger avant l'implémentation :
- L'entité « Minutes » et les deux boutons de la v0.5.0 sont supprimés sans période de transition, tant que le projet reste en `0.x`.
- Les blueprints sont livrés à la racine du dépôt (`blueprints/script/…`) et importés par leur URL GitHub brute ; la raison y est obligatoire, mais l'action `adjust` reste utilisable sans `reason` (« sans motif » dans le rapport).
- La section liste les mouvements manuels de la semaine écoulée (lundi à lundi) avec date, minutes signées et motif, et une ligne par capteur automatique.
- Les mouvements antérieurs à cette version, sans origine, comptent comme manuels dans le premier rapport.
- La liste du rapport est limitée à 30 lignes.
