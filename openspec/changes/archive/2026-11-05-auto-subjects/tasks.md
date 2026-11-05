# Tasks

## 1. Détection

- [x] 1.1 Ajouter `subjects` à `SourceData` et le remplir dans `EcoleDirecteSource` (noms des capteurs de matière, avec ou sans moyenne, puis matières des notes, sans doublon à la normalisation) ; vérifier « Ajout automatique des matières » (matière sans moyenne, orthographe différente) par des tests marqués sur la source
- [x] 1.2 Ajouter au runtime l'ajout automatique : détecter les matières absentes de la table après chaque lecture de la source (activation et bilan), reconstruire la `Config` en mémoire, enregistrer la table dans les options sans recharger l'entrée, utiliser les matières dans le calcul en cours, ne jamais toucher une matière présente (même à 0) ; vérifier « Ajout automatique des matières » (moyenne, note, matière existante inchangée, modifiable ensuite, rien à ajouter) et « Table des matières modifiable » (suppression, matière supprimée mais présente dans la source, matière exclue) par des tests marqués

- [x] 1.3 Ajouter à l'écran *Matières* la case « Détecter les matières de la source » : champ matière obligatoire seulement si la case est décochée, appel de la détection du runtime sans rechargement, message de résultat (matières ajoutées, aucune, source indisponible, aucune source choisie) et traductions fr et en ; vérifier « Détection des matières à la demande » par des tests marqués (détection, nom non exigé, aucune matière à ajouter, source indisponible, aucune source choisie, case décochée) et que les tests existants de l'écran continuent de passer

## 2. Notifications

- [x] 2.1 Publier la notification d'ajout (identifiant propre, sans doublon, textes fr et en, service de notification configuré) et retirer les matières inconnues de la notification d'anomalie (la détection à la demande n'en crée aucune) ; mettre à jour les tests existants de « Notifications » (le scénario « Matière inconnue » vérifie l'ajout automatique) et celui des traductions ; vérifier « Ajout automatique des matières » (notification à l'ajout, aucune matière à ajouter) par des tests marqués

## 3. Documentation

- [x] 3.1 Mettre à jour le `README.md` anglais et français : détection automatique des matières, case à cocher de détection à la demande, multiplicateur 1, notification, 0 pour exclure ; vérifier que le test du README passe

## 4. Intégration

- [x] 4.1 Lancer `uv run pytest` et vérifier que tous les tests passent, y compris le test de couverture des exigences
- [x] 4.2 Relire les « Hypothèses à confirmer » de `design.md` et vérifier que chacune est confirmée par l'utilisateur ou corrigée dans les specs avant l'archivage
- [x] 4.3 À l'archivage, vérifier que `openspec validate --specs --strict` passe

## Workflow follow-up

- Publier une version mineure (version du `manifest.json` et tag `vX.Y.Z`) après l'archivage.
- Vérifier sur l'installation réelle que les matières de la source apparaissent dans la table et que la notification nomme celles à exclure.
