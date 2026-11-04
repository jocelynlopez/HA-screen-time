# Design

## Context

Le point d'extension `GradesSource` existe (`source.py`) avec une `NullSource` par défaut, et le bilan du lundi sait déjà reporter un échec de source. L'intégration `ecole_directe` publie, par enfant, un capteur `…_notes` (attribut `notes` : liste d'entrées avec `date`, `matiere`, `commentaire`, `note`, `sur`, `coefficient`, `non_significatif`, valeurs en texte avec virgule décimale) et un capteur par matière dont l'état est la moyenne et dont les attributs incluent `Nom` et `Code`. Voir `proposal.md` pour la motivation et les specs `ecoledirecte-source`, `grade-conversion`, `screen-time-wallet` et `ha-integration` pour le comportement.

## Goals / Non-Goals

**Goals:**
- Lire ces capteurs sans appel réseau ni dépendance Python, avec une analyse pure et testable.
- Éviter qu'un premier branchement ou un démarrage de HA ne fausse le portefeuille.
- Rendre une panne de source visible.

**Non-Goals:**
- Parler à l'API EcoleDirecte, choisir les capteurs de moyenne à la main, utiliser la moyenne générale d'EcoleDirecte.

## Decisions

- **Analyse pure d'abord** : `ecole_directe_source.py` sépare des fonctions pures (`parse_notes`, `parse_average`) de la lecture des entités (`EcoleDirecteSource.async_fetch`). Les premières sont testées sur les 18 notes réelles ; la seconde avec le registre d'entités de l'instance de test.
- **Découverte des moyennes par le registre d'entités** : on retrouve l'entrée de configuration du capteur de notes, puis les capteurs de cette entrée qui ont les attributs `Nom` et `Code`. Alternative écartée : sélection manuelle de chaque capteur, fastidieuse et à refaire à chaque nouvelle matière ou rentrée.
- **Nom de la matière = attribut `Nom`** du capteur. Il est comparé à la table par normalisation. Pour que `ed.physique & sport.` soit reconnu comme `ED PHYSIQUE & SPORT`, la normalisation ne garde que les lettres et les chiffres (après suppression des accents et de la casse). Alternative écartée : changer la clé du sport dans la table, qui ne réglerait pas les autres écarts d'écriture.
- **Activation d'une source dans le cœur** (`Wallet.activate_source`), pas dans la couche HA : l'opération modifie l'état (notes vues, crédit hebdomadaire, journal) et doit être testée sans HA. Journal : mouvement de type `initialisation`.
- **Marqueur de source activée** : le capteur de notes activé est enregistré dans le stockage de l'entrée (clé `source_entity` à côté de l'état du portefeuille, que `Wallet.from_dict` ignore). Au chargement, si l'option diffère du marqueur, l'activation est tentée ; elle met à jour le marqueur seulement si elle réussit.
- **Une seule file de rattrapage** dans l'objet d'exécution : activation en attente, puis bilan dû. Un échec planifie une nouvelle tentative 5 minutes plus tard (`async_call_later`), 3 fois au plus ; le déclencheur quotidien remet le compteur à zéro. Alternative écartée : attendre le lendemain à chaque échec, qui laisserait le portefeuille sans bilan toute une journée après un redémarrage de HA.
- **Notification de panne seulement si un bilan est dû**, sous un identifiant propre à l'entrée (`…_source`), supprimée au bilan réussi : pas de bruit quand la source est simplement lente à l'activation.
- **Option du capteur** : sélecteur d'entité limité aux capteurs de l'intégration `ecole_directe`, validé contre le registre. Un champ vidé dans le formulaire est absent des données reçues : il est lu comme « aucun capteur ».
- **`after_dependencies`** dans le manifeste, jamais `dependencies`, pour ne pas imposer EcoleDirecte à qui n'utilise pas cette source.

## Risks / Trade-offs

- [Fenêtre d'EcoleDirecte] Le capteur de notes n'affiche que les dernières notes (15 par défaut) → un grand nombre de notes saisies en une semaine pourrait en perdre ; le README conseille d'augmenter « Notes maximum affichées ».
- [Rafraîchissement] EcoleDirecte se met à jour toutes les 30 minutes → une note saisie juste avant minuit est vue au bilan suivant (première vue), jamais perdue.
- [Évolution d'EcoleDirecte] Noms d'attributs ou de capteurs susceptibles de changer → entrées incomplètes ignorées, capteur sans attribut `notes` signalé comme source indisponible.
- [Nom des matières] Seuls les noms d'anglais et de sport sont vérifiés sur des capteurs réels ; les autres sont supposés identiques aux `matiere` des notes → une matière inconnue est notifiée et sans effet.
- [Activation] Remplacer le crédit hebdomadaire par le crédit initial efface ce qui a déjà été consommé dans la semaine d'activation → acceptable pour une opération rare ; elle est journalisée.

## Hypothèses à confirmer

Points que la demande n'a pas tranchés et que les specs écrivent. À valider ou corriger avant l'implémentation :
- Découverte automatique des capteurs de moyenne (attributs `Nom` et `Code`, même entrée EcoleDirecte), sans sélection manuelle.
- Notification persistante quand un bilan dû échoue faute de source, supprimée au bilan réussi.
- Trois nouvelles tentatives espacées de 5 minutes avant d'attendre le déclencheur quotidien.
- L'activation remplace le crédit hebdomadaire par le crédit initial, même en cours de semaine.
- La comparaison des noms de matières ignore la ponctuation et les espaces.
- `ecole_directe` est une dépendance de démarrage facultative (`after_dependencies`).
- Les moyennes sont celles de l'élève lues dans l'état des capteurs de matière (non la moyenne de la classe).
