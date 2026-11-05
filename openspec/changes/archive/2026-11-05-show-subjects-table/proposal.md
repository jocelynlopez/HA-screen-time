# Proposal

## Why

La table des matières et de leurs multiplicateurs n'est visible nulle part dans l'interface : elle n'existe que dans les options de l'entrée. Avec l'ajout automatique des matières, l'utilisateur ne peut donc ni savoir quelles matières ont été ajoutées, ni quel multiplicateur elles ont. Le message « Aucune nouvelle matière : toutes celles de la source sont déjà dans la table » renvoie à une table invisible.

## What Changes

- **Écran des matières** : la table courante est affichée en texte au-dessus du formulaire de *Matières et multiplicateurs*, une ligne par matière avec son multiplicateur.
- **Détection à la demande** : le message de fin (matières ajoutées, ou aucune nouvelle matière) rappelle la table courante.
- **Notification d'ajout automatique** : la notification persistante des matières ajoutées, et le message du service de notification, contiennent aussi la table courante, pour régler les multiplicateurs sans chercher.
- **Présentation** : lignes triées par ordre alphabétique sans tenir compte de la casse ni des accents, multiplicateurs sans zéro superflu (3 et 0,5 en français, 0.5 en anglais).

## Capabilities

### New Capabilities
Aucune.

### Modified Capabilities
- `ha-integration`: affichage de la table des matières à trois endroits de l'interface.

## Impact

- `report.py` (mise en forme de la table, texte de la notification d'ajout), `config_flow.py` (description du pas *Matières* et messages de fin avec la table), `runtime.py` (la notification reçoit la table), `translations/fr.json` et `en.json` (emplacement de la table dans les textes), `README.md`.
- Le cœur (`engine/`) et les specs de calcul ne changent pas ; aucune dépendance.

## Hors périmètre

- Modifier la table directement dans la liste affichée (l'écran reste un formulaire : nom, multiplicateur, suppression, détection).
- Une entité ou un capteur Home Assistant qui exposerait la table.
