# Design

## Context

La table des multiplicateurs est l'option `multipliers` (nom → multiplicateur) de l'entrée. L'écran *Matières* (`async_step_matieres`) est un formulaire dont le texte d'aide est statique dans les traductions. La détection à la demande se termine par `async_abort(reason=…)` : `subjects_added` (avec le placeholder `subjects`) ou `no_new_subjects`. La notification des matières ajoutées est produite par `render_subjects_added` (`report.py`), appelée par le runtime. Aucun de ces textes ne montre la table. Voir `proposal.md` pour la motivation et la spec `ha-integration` pour le comportement.

## Goals / Non-Goals

**Goals:**
- Montrer la table courante là où l'utilisateur la règle ou apprend qu'elle a changé.
- Une seule mise en forme, testée comme fonction pure.

**Non-Goals:**
- Éditer la table dans la liste, ou l'exposer comme entité.

## Decisions

- **Une fonction pure de mise en forme** (`render_subjects_table(table, language)` dans `report.py`) : une ligne Markdown `- NOM : multiplicateur` par matière, triée avec `normalize_subject`, nombres écrits comme dans le rapport (`_number(..., trim=True)` : virgule en français, point en anglais, sans zéro superflu). Elle sert aux trois endroits. Alternative écartée : trois formats différents, sources d'écarts entre l'écran et la notification.
- **Emplacement dans les textes** : un placeholder `{table}` dans le texte d'aide du pas *Matières* et dans les messages `subjects_added` et `no_new_subjects` des traductions ; `async_show_form` et `async_abort` le reçoivent par `description_placeholders`. Le texte de la notification vient de `TEXTS` (`report.py`), qui reçoit la table.
- **Table lue au moment de l'affichage** : à l'ouverture du pas, la table vient des options de l'entrée avec les valeurs par défaut (`with_defaults`) ; après une détection à la demande, `async_detect_subjects` a déjà enregistré les nouvelles matières, la table affichée les contient. Pour la notification d'ajout automatique, le runtime la lit après `_adopt_subjects`, qui a mis les options à jour.
- **Markdown** : les descriptions des formulaires et les notifications persistantes de Home Assistant interprètent le Markdown, d'où la liste à puces ; le message du service de notification reçoit le même texte, lisible même brut.

## Risks / Trade-offs

- [Table longue] Une trentaine de matières allonge l'écran et la notification → acceptable, la liste est en deux colonnes de texte court ; elle reste scrollable dans la fenêtre.
- [Table lue avant l'écriture des options] Si la mise à jour des options échouait, la table affichée serait en retard → la mise à jour est synchrone (`async_update_entry`), la lecture se fait après.
- [Noms avec caractères Markdown] Un nom contenant `*` ou `_` pourrait être mal affiché → les noms EcoleDirecte n'en ont pas ; sinon le défaut est seulement visuel.

## Hypothèses à confirmer

Points que la demande n'a pas tranchés et que les specs écrivent. À valider ou corriger avant l'implémentation :
- La table s'affiche en liste Markdown, une ligne par matière, triée par ordre alphabétique.
- Les multiplicateurs s'écrivent sans zéro superflu, avec la virgule en français et le point en anglais.
- La notification d'ajout automatique contient toute la table, pas seulement les matières ajoutées.
- Le message d'une détection sans nouvelle matière affiche aussi la table.
