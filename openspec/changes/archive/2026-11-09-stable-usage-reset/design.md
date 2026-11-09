# Design

## Décisions

`Baseline` gagne `suspect: bool = False` (sérialisé seulement s'il est vrai ; absent = faux). `consumed_since(baseline, reading, day)` :

1. Pas de référence : première référence, rien consommé (inchangé).
2. Jour connu des deux côtés et différent :
   - relevé égal à la référence et > 0 : relevé périmé → rien consommé, `Baseline(minutes, nouveau jour, suspect=True)` ;
   - sinon remise à zéro comme avant.
3. Même jour connu, relevé < référence :
   - référence suspecte : remise à zéro confirmée, le relevé est consommé, `suspect=False` ;
   - sinon : rien consommé, référence inchangée avec `suspect=True`.
4. Sans date d'un côté, relevé < référence : remise à zéro immédiate (inchangé).
5. Relevé ≥ référence : consommation de la différence, `suspect=False`.

Cas minuit : référence (40, J1) ; relevé 40 daté J2 → périmé, référence (40, J2, suspecte) ; relevé réel 0 → baisse confirmée, rien consommé ; relevé réel 3 → 3 consommées.
Cas relevé bas : 46 → 36 → 46 : rien consommé au relevé 36, doute annulé au retour à 46.

Rapport : la constante `MAX_MANUAL_LINES` et la ligne « … et N autre(s) » sont supprimées ; le journal reste borné à 200 mouvements.

## Hypothèses à confirmer

1. Une vraie remise à zéro en milieu de journée est consommée avec un relevé de retard, et une baisse passagère de plus d'un relevé consécutif reste recomptée (la confirmation se fait sur deux relevés).
2. Sans attribut `date` (référence ou relevé), l'ancien comportement est conservé.
3. Aucun rattrapage automatique du solde : l'utilisateur rend les minutes avec `adjust`.
4. La longueur du rapport n'est plus bornée par l'intégration (au plus 200 mouvements du journal) ; une notification ou un service `notify` qui limiterait la taille est hors périmètre.
5. Version patch `0.9.1`.
