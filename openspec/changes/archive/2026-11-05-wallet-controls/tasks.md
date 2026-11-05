# Tasks

## 1. Commandes

- [x] 1.1 Extraire la construction de l'appareil dans un module partagé (utilisé par les capteurs) et ajouter `control_minutes` (15) au runtime ; vérifier que les tests des capteurs existants passent
- [x] 1.2 Ajouter `number.py` : entité « Minutes » (1 à 600, pas 5, restaurée au redémarrage), plateforme `number` dans `PLATFORMS`, textes fr et en ; vérifier « Commandes du portefeuille » (valeur par défaut, valeur conservée au redémarrage, valeur hors limites, appareil de l'enfant) par des tests marqués
- [x] 1.3 Ajouter `button.py` : « Ajouter du temps » (ajustement) et « Retirer du temps » (consommation) avec le motif « bouton », plateforme `button` dans `PLATFORMS`, textes fr et en ; vérifier « Commandes du portefeuille » (ajouter, retirer, retrait supérieur au temps disponible, blocage déclenché par le bouton) par des tests marqués

## 2. Documentation

- [x] 2.1 Mettre à jour le `README.md` anglais et français : les trois commandes, leur effet, le motif du journal ; vérifier que les tests du README et des traductions passent

## 3. Intégration

- [x] 3.1 Lancer `uv run pytest` et vérifier que tous les tests passent, y compris le test de couverture des exigences
- [x] 3.2 Relire les « Hypothèses à confirmer » de `design.md` et vérifier que chacune est confirmée par l'utilisateur ou corrigée dans les specs avant l'archivage
- [x] 3.3 À l'archivage, vérifier que `openspec validate --specs --strict` passe

## Workflow follow-up

- Publier une version mineure (version du `manifest.json` et tag `vX.Y.Z`) après l'archivage.
- Vérifier sur l'installation réelle que l'entité et les boutons apparaissent sur l'appareil de l'enfant et qu'ils déclenchent le blocage.
