# Proposal

## Why

Aujourd'hui, une matière absente de la table des multiplicateurs n'a aucun effet : ses moyennes et ses notes sont ignorées et seulement signalées. L'utilisateur doit donc saisir à la main, dans *Configurer → Matières et multiplicateurs*, chaque matière que la source EcoleDirecte publie déjà dans ses capteurs. Ce change fait détecter ces matières automatiquement et les ajoute à la table avec le multiplicateur 1, modifiable ensuite.

## What Changes

- **Détection** : à l'activation d'une source et avant chaque bilan, les matières présentes dans les données de la source (capteurs de moyenne par matière, avec ou sans moyenne, et notes) sont comparées à la table.
- **Ajout automatique** : chaque matière absente est ajoutée dans les options avec le multiplicateur 1, sous le nom écrit par la source, puis utilisée dans le calcul en cours. Une matière déjà présente, même à 0, reste inchangée.
- **Notification à l'ajout** : une notification persistante nomme les matières ajoutées et invite à régler leur multiplicateur ; le service de notification configuré reçoit le même message.
- **Détection à la demande** : une case « Détecter les matières de la source » dans la fenêtre *Matières et multiplicateurs* lance la même détection sans saisir de nom, et affiche le résultat dans la fenêtre. Home Assistant n'offre pas de vrai bouton dans un formulaire d'options : la case à cocher en est l'équivalent.
- **Table modifiable** : supprimer une matière qui existe encore dans la source la fait réapparaître avec le multiplicateur 1 au prochain ajout automatique ; pour l'exclure du calcul, on lui donne le multiplicateur 0.
- **Plus d'alerte « matière inconnue »** : une matière de la source n'est plus inconnue, la notification d'anomalie ne signale donc plus que les notes rejetées.

## Capabilities

### New Capabilities
Aucune.

### Modified Capabilities
- `ha-integration`: ajout automatique des matières de la source, notification à l'ajout, détection à la demande, table des matières modifiable (suppression et exclusion), notifications d'anomalie sans les matières inconnues.

## Impact

- `source.py` (`SourceData` gagne la liste des matières), `ecole_directe_source.py` (matières des capteurs et des notes), `runtime.py` (détection, mise à jour des options, notification), `config_flow.py` (case à cocher et résultat), `__init__.py` (l'écouteur d'options ne recharge pas pour un ajout automatique), `report.py` et `translations` (message d'ajout, anomalies sans matières inconnues), `README.md`.
- Le cœur (`engine/`) ne change pas : une matière absente de la table y garde le multiplicateur 0 ; l'ajout se fait avant le calcul, dans la couche Home Assistant.
- Aucune dépendance, aucun appel réseau.

## Hors périmètre

- Un vrai bouton (entité *button* ou service) pour la détection à la demande.
- Détection à chaque changement de capteur en cours de semaine (elle a lieu à l'activation et avant chaque bilan).
- Interface listant la table des matières existantes ; l'écran *Matières* reste un champ à saisir.
- Suppression automatique des matières qui disparaissent de la source.
