# Tasks

## 1. Cœur

- [ ] 1.1 Créer `engine/usage.py` : `consumed_since(référence, relevé)` (partie entière de la différence, référence avancée des minutes consommées, premier relevé sans consommation, baisse = remise à zéro, relevé invalide ignoré) ; vérifier « Consommation entre deux relevés », « Premier relevé », « Remise à zéro du compteur » et « Relevé invalide ignoré » par des tests marqués (15 minutes, fractions 10,6 puis 11,2, 190 → 12, 190 → 0, indisponible, négatif)
- [ ] 1.2 Ajouter le paramètre `merge` à `Wallet.consume` (regroupement dans le dernier mouvement de consommation de même motif et de même jour) ; vérifier « Regroupement des consommations automatiques » par des tests marqués (trois relevés, jour différent, motif différent, consommation manuelle) et que les tests existants de la consommation passent

## 2. Intégration

- [ ] 2.1 Ajouter l'option des capteurs de temps d'écran (sélecteur multiple de capteurs, validation contre le registre, champ vidé = aucun capteur) et ses traductions ; vérifier « Capteurs de temps d'écran » par des tests marqués (choix, entité inexistante, aucun par défaut)
- [ ] 2.2 Suivre les changements d'état des capteurs choisis : référence initiale au premier relevé, consommation automatique avec le nom du capteur pour motif, enregistrement et mise à jour des entités, références des capteurs retirés oubliées ; vérifier « Consommation automatique » et le scénario « Capteur retiré puis rajouté » par des tests marqués (relevé, deux capteurs, indisponible, remise à zéro, usage supérieur au crédit)
- [ ] 2.3 Enregistrer les références avec l'état, les restaurer et relever chaque capteur au démarrage après le bilan ; vérifier « Relevés de référence conservés » par des tests marqués (redémarrage, remise à zéro pendant l'arrêt, rechargement par les options)

## 3. Documentation

- [ ] 3.1 Mettre à jour le `README.md` : choix des capteurs de temps d'écran, fonctionnement de la référence et de la remise à zéro, journal regroupé, limites ; vérifier que le test du README et celui des traductions passent

## 4. Intégration

- [ ] 4.1 Lancer `uv run pytest` et vérifier que tous les tests passent, y compris le test de couverture des exigences
- [ ] 4.2 Relire les « Hypothèses à confirmer » de `design.md` et vérifier que chacune est confirmée par l'utilisateur ou corrigée dans les specs avant l'archivage
- [ ] 4.3 À l'archivage, vérifier que `openspec validate --specs --strict` passe

## Workflow follow-up

- Installer `microsoft_family_safety`, choisir `sensor.{appareil}_screen_time` dans les options et observer, dans le journal, le comportement du compteur à sa remise à zéro.
