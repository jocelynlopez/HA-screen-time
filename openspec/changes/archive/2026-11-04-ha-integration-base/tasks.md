# Tasks

## 1. Réorganisation du dépôt

- [x] 1.1 Déplacer `src/portefeuille_minutes/` vers `custom_components/screen_time_wallet/engine/` (avec `git mv`), créer un `__init__.py` léger pour `custom_components/screen_time_wallet/`, et adapter les imports des tests ; vérifier que les 86 tests existants passent
- [x] 1.2 Simplifier `pyproject.toml` : projet non packagé, `requires-python >=3.14.2`, `pytest-homeassistant-custom-component` en dépendance de développement, `pythonpath` pour `custom_components` ; vérifier avec `uv sync` puis `uv run pytest`

## 2. Cœur : journal, ajustement, sérialisation (`screen-time-wallet`)

- [x] 2.1 Ajouter le journal des mouvements (type, date, variations, motif, 200 maximum) alimenté par le bilan, la consommation et l'ajustement ; vérifier « Journal des mouvements » par des tests marqués (bilan, consommation, journal borné)
- [x] 2.2 Ajouter l'ajustement manuel sur le capital notes avec rejet d'un montant nul ; vérifier « Ajustement manuel » par des tests marqués
- [x] 2.3 Ajouter l'export et la restauration de l'état (clés de notes comprises, version 1, version inconnue refusée) ; vérifier « État sérialisable » par des tests marqués (aller-retour, notes déjà vues conservées, version inconnue)

- [x] 2.4 Étendre le compte rendu du bilan aux éléments du calcul (nombre de matières, moyenne générale, poids, moyenne de la semaine, repli, capital notes et temps disponible après le bilan) ; vérifier « Compte rendu du bilan » par des tests marqués (compte rendu complet, éléments du calcul, crédit de repli)

## 3. Squelette de l'intégration

- [x] 3.1 Créer `manifest.json` (domaine, flux de configuration, mode `calculated`, version 0.1.0), `hacs.json` à la racine et `const.py` ; vérifier « Métadonnées d'installation » par des tests marqués
- [x] 3.2 Créer le flux de configuration (nom de l'enfant, refus d'un doublon), le chargement et le déchargement d'une entrée, l'objet d'exécution du portefeuille et son stockage ; vérifier « Un portefeuille par entrée de configuration » par des tests marqués (création, doublon, deux enfants indépendants)
- [x] 3.3 Enregistrer l'état après chaque changement et le restaurer au démarrage, avec refus d'un stockage illisible ; vérifier « Persistance de l'état » par des tests marqués (redémarrage, premier démarrage, stockage illisible)

## 4. Options

- [x] 4.1 Créer la conversion pure des options (heures → minutes, pourcentage → fraction) et le flux d'options des paramètres avec validation ; vérifier « Options modifiables dans l'interface » par des tests marqués (heures, pourcentage, valeur refusée, état conservé après modification, valeurs par défaut dont le rapport hebdomadaire activé)
- [x] 4.2 Créer l'étape d'options de la table des matières (ajout, modification, suppression, table vide refusée) ; vérifier « Table des matières modifiable » par des tests marqués

## 5. Bilan, source et notifications

- [x] 5.1 Définir le protocole `GradesSource` et la source nulle ; vérifier « Source de moyennes et de notes » par des tests marqués (sans source, source disponible, source en erreur)
- [x] 5.2 Brancher le bilan : déclencheur quotidien à 00h00 locale et rattrapage au chargement, avec enregistrement ; vérifier « Bilan automatique du lundi » par des tests marqués (lundi, autre jour, lundis manqués) en avançant l'horloge de test
- [x] 5.3 Envoyer la notification persistante et le service `notify` optionnel pour les matières inconnues et les notes rejetées ; vérifier « Notifications » par des tests marqués (matière inconnue, note rejetée, service configuré, aucune anomalie)

- [x] 5.4 Écrire la fonction pure qui met en forme le rapport hebdomadaire à partir du compte rendu, le publier après chaque bilan (notification distincte, service `notify`, un seul message pour les lundis rattrapés, option de désactivation) ; vérifier « Rapport hebdomadaire » par des tests marqués (contenu, semaine sans note, repli, lundis manqués, service de notification, rapport désactivé)

## 6. Entités et services

- [x] 6.1 Créer les quatre capteurs avec leurs unités et leur rafraîchissement par signal ; vérifier « Capteurs du portefeuille » par des tests marqués (temps disponible, mise à jour après consommation, dernier bilan)
- [x] 6.2 Exposer le journal en attribut (20 mouvements, du plus récent au plus ancien) ; vérifier « Journal des mouvements exposé » par des tests marqués
- [x] 6.3 Créer les services `consume` et `adjust` (`services.yaml`, validation des montants, enregistrement de l'état) ; vérifier « Service de consommation » et « Service d'ajustement manuel » par des tests marqués

## 7. Traductions et documentation

- [x] 7.1 Écrire les traductions françaises et anglaises (flux, options, entités, services, erreurs) ; les libellés du rapport restent dans `report.py` en deux langues ; vérifier « Traductions » par des tests marqués qui comparent les clés des deux langues, celles des libellés du rapport et la présence de toutes les clés utilisées par le code
- [x] 7.2 Écrire un `README.md` (installation par HACS ou copie dans `config/custom_components/`, configuration, services) ; vérifier que les noms de services et d'options cités existent dans le code

## 8. Intégration

- [x] 8.1 Lancer `uv run pytest` et vérifier que tous les tests passent, y compris le test de couverture des exigences
- [x] 8.2 Relire les « Hypothèses à confirmer » de `design.md` et vérifier que chacune est confirmée par l'utilisateur ou corrigée dans les specs avant l'archivage
- [x] 8.3 À l'archivage, vérifier que `openspec validate --specs --strict` passe

## Workflow follow-up

- Installer l'intégration sur le Home Assistant Container de l'utilisateur et la tester en réel (ajout de l'entrée, options, services) : hors des tests automatiques.
