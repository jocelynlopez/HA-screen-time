# Tasks

## 1. Traçabilité exigence → test

- [x] 1.1 Faire lire par `tests/test_requirements_coverage.py` les exigences effectives : specs principales, moins les `REMOVED`, plus les `ADDED` et `MODIFIED` des deltas des changes actifs ; vérifier par un test du lecteur (specs temporaires) que les trois cas sont gérés
- [x] 1.2 Vérifier que le test de couverture échoue quand un marqueur est retiré ou renommé, puis restaurer le fichier

## 2. Configuration et taux (`weekly-credit`)

- [x] 2.1 Remplacer les paramètres de `config.py` : temps maximal 1200, part des notes 0,6, pivot 12, table des multiplicateurs aux noms d'EcoleDirecte, poids minimal 3, nombre minimal de matières 4, crédit de repli 240, option d'exclusion des notes non significatives ; vérifier « Paramètres configurables » par des tests marqués (valeurs par défaut, valeur modifiée)
- [x] 2.2 Exposer les taux déduits de la moyenne et de la semaine et rejeter une configuration dont la somme des multiplicateurs est nulle ou dont le pivot est ≥ 20 ; vérifier « Taux déduits du maximum et du ratio » par des tests marqués (taux par défaut, maximum 480 + 720 = 1200, configuration invalide)

## 3. Notes (`grade-conversion`)

- [x] 3.1 Réécrire `grades.py` : note avec date, matière, commentaire, valeur, barème, coefficient et indicateur non significatif ; lecture tolérante de la virgule décimale ; supprimer la conversion en minutes ; vérifier « Normalisation du barème » (8/10 → 16, 4,5/5 → 18, 2/15 → 2,67)
- [x] 3.2 Implémenter la reconnaissance d'une matière par son nom d'EcoleDirecte (casse et accents ignorés), le multiplicateur 0 et le signalement d'une matière inconnue ; vérifier « Multiplicateur par matière » (matière classée, non classée, casse et accents, table modifiée)
- [x] 3.3 Implémenter le poids d'une note et la reconnaissance d'une note non numérique ; vérifier « Poids d'une note » et « Note non numérique » par des tests marqués
- [x] 3.4 Implémenter la validation des notes (barème, valeur, coefficient) avec signalement d'une erreur explicite ; vérifier « Rejet des notes invalides » par des tests marqués
- [x] 3.5 Implémenter la clé d'une note (date, matière normalisée, commentaire, barème, coefficient) et vérifier sur les 18 notes réelles de l'échantillon que les clés sont distinctes, y compris « Attitude » et « Participation »

## 4. Crédits (`weekly-credit`)

- [x] 4.1 Créer `credit.py` : moyenne générale pondérée et crédit initial avec plancher à 0 et repli ; vérifier « Moyenne générale pondérée » et « Crédit initial » par des tests marqués (sept matières → 228, tout à 20 → 480, moyenne ≤ 12 → 0, trois matières → 240, quatre matières → formule)
- [x] 4.2 Implémenter la moyenne de la semaine avec complétion au poids minimal et l'exclusion optionnelle des notes non significatives ; vérifier « Moyenne de la semaine » et « Notes non significatives » par des tests marqués
- [x] 4.3 Implémenter le crédit de semaine et l'arrondi demi éloigné de zéro ; vérifier « Crédit de semaine » et « Arrondi des crédits » par des tests marqués (+342 sans note, −374, −450, +720, +180 pour cinq 14/20, 0 sous le repli, ±0,5 → ±1)

## 5. Portefeuille (`screen-time-wallet`)

- [x] 5.1 Réécrire `wallet.py` : crédit hebdomadaire, capital notes, temps disponible et initialisation avec mémorisation des notes visibles ; vérifier « Deux compartiments » et « Initialisation du portefeuille » par des tests marqués
- [x] 5.2 Implémenter le bilan du lundi avec date injectée, idempotence et lundis manqués ; vérifier « Bilan du lundi » et « Lundis manqués » par des tests marqués (non cumulable, capital cumulé, avant lundi, bilan répété, trois lundis)
- [x] 5.3 Implémenter les notes de la semaine (notes vues pour la première fois, première valeur conservée) et les notes écartées ou signalées ; vérifier « Notes de la semaine » et « Notes écartées ou signalées » par des tests marqués
- [x] 5.4 Implémenter le compte rendu du bilan et la consommation (crédit hebdomadaire d'abord, puis capital notes, rejet des montants ≤ 0) ; vérifier « Compte rendu du bilan » et « Consommation » par des tests marqués
- [x] 5.5 Rejouer les 18 notes réelles de l'échantillon par un test de bout en bout, avec pour chaque lundi du 21/09 au 09/11 les moyennes par matière calculées dans la simulation validée (à reproduire dans les données du test), et vérifier la séquence attendue : crédit initial 228 pour les sept moyennes actuelles, crédit de semaine −374 au bilan du 09/11, capital notes cumulé de +972 à cette date

## 6. Intégration

- [x] 6.1 Lancer `uv run pytest` et vérifier que tous les tests passent, y compris le test de couverture des exigences
- [x] 6.2 Relire les « Hypothèses à confirmer » de `design.md` et vérifier que chacune est confirmée par l'utilisateur ou corrigée dans les specs avant de passer à l'archivage
- [x] 6.3 À l'archivage, mettre à jour la section Purpose de la spec principale `grade-conversion` (elle décrit encore une conversion en minutes) et vérifier que `openspec validate --specs --strict` passe
