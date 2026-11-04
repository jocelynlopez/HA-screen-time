# Tasks

## 1. Cœur

- [x] 1.1 Rendre la normalisation des noms de matières insensible à la ponctuation et aux espaces (lettres et chiffres seulement) ; vérifier « Multiplicateur par matière » par des tests marqués (ponctuation, `ANGLAIS LV1` et `ANGLAIS LV2` distincts) et que les anciens tests passent
- [x] 1.2 Ajouter `Wallet.activate_source` (notes visibles mémorisées sans effet, crédit hebdomadaire remplacé par le crédit initial, capital et dernier bilan inchangés, mouvement `initialisation` journalisé) ; vérifier « Activation d'une source » par des tests marqués (notes mémorisées, crédit remplacé, moins de quatre matières)

## 2. Source EcoleDirecte (`ecoledirecte-source`)

- [x] 2.1 Créer les fonctions pures d'analyse des notes et des moyennes (virgule décimale, entrées incomplètes ignorées, valeur non numérique transmise, état non numérique ignoré) ; vérifier « Lecture des notes » et « Moyenne indisponible » par des tests marqués, dont la traduction des 18 notes réelles
- [x] 2.2 Créer `EcoleDirecteSource` : lecture du capteur de notes, découverte des capteurs de moyenne par le registre d'entités (même entrée, attributs `Nom` et `Code`, autres entrées et capteur de notes exclus), erreur de source si le capteur est absent, indisponible ou sans attribut `notes` ; vérifier « Découverte des moyennes par matière » et « Capteur de notes indisponible » par des tests marqués avec deux entrées EcoleDirecte simulées

## 3. Intégration

- [x] 3.1 Ajouter l'option du capteur de notes (sélecteur limité à `ecole_directe`, validation contre le registre, champ vidé = aucun capteur) et ses traductions ; vérifier les scénarios ajoutés à « Options modifiables dans l'interface » par des tests marqués
- [x] 3.2 Brancher la source choisie à l'exécution et mémoriser le capteur activé dans le stockage ; activer la source au premier choix et au changement, pas au rechargement ; vérifier « Activation de la source » par des tests marqués (première sélection, changement, rechargement, source pas prête)
- [x] 3.3 Planifier les nouvelles tentatives (5 minutes, 3 fois, compteur remis à zéro au déclencheur quotidien) pour le bilan et l'activation ; vérifier les scénarios « Nouvelles tentatives » et « Tentatives épuisées » de « Source de moyennes et de notes » par des tests marqués en avançant l'horloge
- [x] 3.4 Créer la notification de source indisponible quand un bilan dû échoue (sans doublon, supprimée au bilan réussi, absente si aucun bilan n'est dû) et ses libellés français et anglais ; vérifier « Source indisponible signalée » par des tests marqués
- [x] 3.5 Déclarer `ecole_directe` en `after_dependencies` dans le manifeste ; vérifier « Ordre de chargement » par un test marqué

## 4. Documentation

- [x] 4.1 Mettre à jour le `README.md` : choix du capteur de notes, découverte des moyennes, conseil d'augmenter « Notes maximum affichées » dans EcoleDirecte, notification de source indisponible ; vérifier que le test du README et celui des traductions passent

## 5. Intégration

- [x] 5.1 Lancer `uv run pytest` et vérifier que tous les tests passent, y compris le test de couverture des exigences
- [x] 5.2 Relire les « Hypothèses à confirmer » de `design.md` et vérifier que chacune est confirmée par l'utilisateur ou corrigée dans les specs avant l'archivage
- [x] 5.3 À l'archivage, vérifier que `openspec validate --specs --strict` passe

## Workflow follow-up

- Brancher le capteur `sensor.ed_mael_lopez_notes` sur le Home Assistant réel et vérifier le premier rapport du lundi.
