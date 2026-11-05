# Proposal

## Why

Donner ou retirer du temps à la main passe aujourd'hui par les actions `screen_time_wallet.adjust` et `screen_time_wallet.consume`, qu'il faut écrire en YAML et diriger vers un capteur du portefeuille. C'est lourd pour tester le blocage ou corriger un solde. Ce change ajoute, sur l'appareil de chaque enfant, des commandes utilisables directement depuis l'interface ou le tableau de bord.

## What Changes

- **Entité « Minutes »** : une entité numérique règle le nombre de minutes à utiliser (de 1 à 600, par pas de 5, 15 par défaut). Sa valeur est conservée au redémarrage.
- **Bouton « Ajouter du temps »** : ajuste le capital notes de + N minutes (même effet que l'action `adjust`, motif « bouton »).
- **Bouton « Retirer du temps »** : consomme N minutes, crédit hebdomadaire d'abord (même effet que l'action `consume`, motif « bouton »).
- **Blocage automatique** : les boutons passent par les mêmes opérations que les actions, donc le temps disponible, le journal, les capteurs et le blocage automatique se mettent à jour comme d'habitude.
- Les actions `consume` et `adjust` restent disponibles.

## Capabilities

### New Capabilities
Aucune.

### Modified Capabilities
- `ha-integration`: commandes numériques et boutons du portefeuille.

## Impact

- Nouveaux fichiers `number.py` et `button.py` dans `custom_components/screen_time_wallet/`, plateformes `number` et `button` ajoutées à `PLATFORMS`, un module partagé pour les informations d'appareil (utilisé aussi par les capteurs), `runtime.py` (valeur des minutes partagée), traductions fr et en, `report.py` (motif du journal), `README.md`.
- Le cœur (`engine/`) ne change pas. Aucune dépendance.

## Hors périmètre

- Bouton de test du blocage : « Retirer du temps » suffit.
- Carte de tableau de bord ou jauge (change `weekly-gauge` à part).
- Motif de journal personnalisable depuis les boutons.
