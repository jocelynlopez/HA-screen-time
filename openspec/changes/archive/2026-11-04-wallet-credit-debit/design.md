# Design

## Context

Projet Python (uv, pytest) sans dépendance runtime. La logique est pure : pas d'I/O, pas d'accès réseau, pas d'horloge système implicite. Les besoins sont décrits dans `proposal.md` et les specs `grade-conversion` et `screen-time-wallet`.

## Goals / Non-Goals

**Goals:**
- Logique métier déterministe et testable : la date courante est toujours fournie en paramètre.
- Chaque exigence de la spec est vérifiée par au moins un test pytest, et le lien exigence → test est lisible.

**Non-Goals:**
- Persistance, interface, connexion à EcoleDirecte.

## Decisions

- **Paramètres regroupés dans un objet de configuration immuable** (taux de base, pivot, allocation, table des multiplicateurs), avec les valeurs de la spec par défaut. Alternative écartée : constantes de module, car tu veux ajuster les valeurs à l'usage et les tests doivent pouvoir les surcharger.
- **Arithmétique exacte avec `Fraction` ou `Decimal`** pour les notes et coefficients décimaux, puis arrondi demi-éloigné de zéro. Alternative écartée : `float` et `round()`, car l'arrondi bancaire de Python donnerait 8 pour 7,5 mais 2 pour 2,5, ce qui contredit la spec, et les flottants produisent des demi-minutes inexactes.
- **Temps injecté** : les opérations qui dépendent de la date reçoivent un `datetime`. Les lundis 00h00 sont calculés en heure locale naïve. Alternative écartée : `datetime.now()`, non testable.
- **Traçabilité exigence → test** : un marqueur pytest `requirement("<capability>/<nom de l'exigence>")` sur chaque test, avec une vérification automatique que chaque exigence de la spec est référencée au moins une fois.

## Risks / Trade-offs

- [Dérive spec / code] → un test de couverture des exigences échoue si une exigence de la spec n'a aucun test.
- [Fuseau horaire et changement d'heure] → heure locale naïve, suffisant pour un usage familial. À revoir si la persistance est ajoutée.

## Hypothèses confirmées

Points que la demande n'avait pas tranchés, validés par l'utilisateur et écrits dans les specs :
- À la création, l'allocation de la semaine en cours est créditée (solde initial = 240).
- Le nom de matière est insensible à la casse et aux accents.
- Une note déjà traitée est ignorée même si ses valeurs ont changé (la première gagne, pas de différence appliquée).
- Une note invalide (hors barème, coefficient négatif) lève une erreur.
- Une note non numérique (absent, dispensé, non noté) est ignorée sans erreur ; son identifiant n'est pas marqué comme traité.
