# Design

## Context

Le projet est un paquet Python sans dépendance runtime (uv, pytest). Le code livré par le change précédent (`config.py`, `grades.py`, `wallet.py`) calcule un montant par note et une allocation fixe : tout cela est remplacé. La logique reste pure : pas d'I/O, pas d'horloge implicite, pas d'accès à Home Assistant ni à EcoleDirecte. Voir `proposal.md` pour la motivation et les specs `weekly-credit`, `grade-conversion` et `screen-time-wallet` pour le comportement.

Les données réelles viennent des capteurs de l'intégration EcoleDirecte : une liste de notes (champs `date`, `matiere`, `commentaire`, `note`, `sur`, `coefficient`, `non_significatif`, valeurs en texte avec virgule décimale, sans identifiant) et un capteur de moyenne par matière.

## Goals / Non-Goals

**Goals:**
- Un cœur déterministe et testable : tout paramètre est une valeur de configuration, toute date est injectée.
- Les moyennes par matière sont une entrée du bilan, pas un calcul interne.
- Chaque exigence des specs est vérifiée par au moins un test marqué `requirement`.

**Non-Goals:**
- Intégration Home Assistant, persistance, notifications, lecture des capteurs.
- Calcul des moyennes à partir des notes : EcoleDirecte les fournit déjà et exclut les notes non significatives.

## Decisions

- **Calculs exacts avec `Fraction`**, arrondi final une seule fois par crédit (demi éloignée de zéro). Alternative écartée : `float` ou `round()` de Python, dont l'arrondi bancaire contredit la spec.
- **Trois modules** : `config.py` (paramètres et taux déduits), `grades.py` (normalisation, poids, validité, clé de note), `credit.py` (moyenne générale, crédit initial, moyenne de la semaine, crédit de semaine), plus `wallet.py` (compartiments, bilan, consommation). Alternative écartée : tout dans `wallet.py`, qui mélangerait formules et état.
- **Taux déduits, pas stockés** : `Config` stocke le temps maximal, la part des notes et le pivot, et expose les taux calculés. Ainsi changer le maximum ou le ratio, depuis l'interface HA plus tard, suffit.
- **Moyennes en entrée du bilan** : `settle(now, averages, notes)` reçoit un dictionnaire matière → moyenne sur 20. Alternative écartée : recalculer les moyennes depuis les notes, qui ne couvrent que les 15 à 18 dernières et qui diffèrent de celles d'EcoleDirecte (notes non significatives).
- **Clé de note calculée** : `(date, matière normalisée, commentaire, barème, coefficient)` sans la valeur, car EcoleDirecte n'expose pas d'identifiant. Vérifiée sur 18 notes réelles : 18 clés distinctes. Risque assumé : deux évaluations identiques le même jour dans la même matière seraient confondues.
- **Notes de la semaine = notes vues pour la première fois** depuis le dernier bilan, plutôt que par `date_saisie`, pour ne perdre aucune note publiée en retard.
- **Une note devient « vue » seulement quand elle a pu être comptée ou qu'elle est sans effet par construction** : une note non numérique ou invalide n'est pas marquée, ce qui permet de la compter plus tard si sa valeur arrive.
- **Temps en heure locale naïve** : le lundi 00h00 est calculé sans fuseau, suffisant pour un usage familial.
- **Traçabilité** : même marqueur pytest `requirement("<capability>/<exigence>")`. Le test de couverture lit aussi les deltas des changes actifs (ADDED et MODIFIED ajoutent, REMOVED retire), car les specs principales ne sont mises à jour qu'à l'archivage.

## Risks / Trade-offs

- [Amplitude des crédits] Avec 20 h au maximum, un seul 7/20 en français coûte −450 min, soit deux fois le crédit initial de 228 → voulu, vérifié sur les données réelles, tous les paramètres restent réglables.
- [Début d'année] Sous 4 matières avec moyenne, le crédit de semaine vaut 0 et les notes de ces semaines sont marquées vues sans effet → elles ne seront jamais comptées ; acceptable, c'est le coût de la règle des 4 matières.
- [Dette durable] Le capital notes négatif persiste jusqu'à ce que de bonnes notes le compensent → conforme à la demande, sans plafond.
- [Données EcoleDirecte] Intégration non officielle, noms de matières et formats pouvant changer → la matière inconnue est signalée, les valeurs textuelles sont lues de façon tolérante.

## Hypothèses à confirmer

Points que les échanges n'ont pas tranchés et que les specs écrivent. À valider ou corriger avant l'implémentation :
- **Note invalide** : rejetée et signalée sans interrompre le bilan, au lieu de lever une erreur bloquante comme dans la décision précédente. Un lot de notes ne doit pas empêcher le bilan du lundi.
- **Lundis manqués** : un bilan par lundi, les notes en attente rattachées au premier ; les suivants valent une semaine sans note.
- **Plafond du capital notes** : aucun. La question posée en fin d'échange est restée sans réponse ; ce change n'en ajoute pas.
- **Nom du sport** : la table utilise `ED PHYSIQUE & SPORT`, déduit du nom du capteur ; aucune note de sport n'a encore permis de vérifier le nom exact. Une matière inconnue est signalée, donc l'erreur serait visible.
- **Matières à multiplicateur 0** : elles ne comptent ni dans la moyenne générale ni dans le nombre minimal de matières.
- **Premier bilan** : le dernier bilan d'un portefeuille neuf est le lundi de sa semaine de création.
