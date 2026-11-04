# Tasks

## 1. Traçabilité exigence → test

- [x] 1.1 Ajouter le marqueur pytest `requirement("<capability>/<exigence>")` (enregistré dans `pyproject.toml`) et vérifier que `uv run pytest --strict-markers` l'accepte
- [x] 1.2 Ajouter un test qui lit les `### Requirement:` des specs de `openspec/changes/wallet-credit-debit/specs/` et échoue si une exigence n'est référencée par aucun marqueur ; vérifier qu'il échoue quand une exigence est volontairement retirée

## 2. Conversion des notes (`grade-conversion`)

- [x] 2.1 Implémenter la configuration (taux de base 15, pivot 12, allocation 240, table des multiplicateurs) et vérifier les exigences « Note pivot », « Taux de base » et « Multiplicateur par matière » par des tests marqués
- [x] 2.2 Implémenter la formule, la normalisation du barème, le coefficient décimal et l'arrondi demi-éloigné de zéro ; vérifier les exigences « Formule de conversion », « Normalisation du barème », « Coefficient » et « Arrondi » par des tests marqués (scénarios +7,5 → +8 et −7,5 → −8 inclus)
- [x] 2.3 Implémenter la reconnaissance de matière sans casse ni accents et le multiplicateur 0 pour une matière inconnue ; vérifier les scénarios correspondants
- [x] 2.4 Implémenter le rejet des notes invalides ; vérifier l'exigence « Rejet des notes invalides » par des tests marqués

## 3. Portefeuille (`screen-time-wallet`)

- [x] 3.1 Implémenter le solde, l'allocation à la création et l'allocation hebdomadaire du lundi 00h00 avec date injectée, rattrapage de plusieurs semaines et mise à jour idempotente ; vérifier les exigences « Solde en minutes entières », « Allocation à la création », « Allocation hebdomadaire » et « Report du solde » par des tests marqués
- [x] 3.2 Implémenter l'application d'une note au solde, le refus du double traitement par identifiant, l'ignorance des notes non numériques et le rejet atomique d'une note invalide ; vérifier les exigences « Application d'une note au solde », « Pas de double traitement d'une note », « Note non numérique ignorée » et « Rejet atomique d'une note invalide » par des tests marqués

## 4. Intégration

- [x] 4.1 Lancer `uv run pytest` et vérifier que tout passe, y compris le test de couverture des exigences de 1.2
- [x] 4.2 Relire les « Hypothèses » de `design.md` et vérifier que chacune est confirmée dans les specs (confirmé par l'utilisateur, spec « Note non numérique ignorée » ajoutée avant le code)
