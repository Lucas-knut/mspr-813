# Questions Metabase — Electio-Analytics

Questions pertinentes à poser dans Metabase pour analyser les données électorales France métropolitaine.

---

## Table `gold_france.features_communes` (données historiques 2002–2022)

### Vue d'ensemble électorale

**Q1 — Évolution temporelle des blocs**
- Résumer : Moyenne de `pct_gauche`, `pct_centre`, `pct_droite`, `pct_extremedroite`
- Grouper par : `annee`
- Type de graphique : Lignes

**Q2 — Répartition des blocs dominants par année**
- Résumer : Nombre de lignes
- Grouper par : `annee`, `bloc_dominant`
- Type de graphique : Barres empilées

**Q3 — Communes par bloc dominant en 2022**
- Filtrer : `annee = 2022`
- Colonnes : `code_commune`, `libelle`, `code_dep`, `bloc_dominant`
- Type de graphique : Tableau

### Analyse sociodémographique

**Q4 — CSP par bloc dominant (2022)**
- Filtrer : `annee = 2022`
- Grouper par : `bloc_dominant`
- Résumer : Moyenne de `cadres_pct`, `ouvriers_pct`, `employes_pct`, `artisans_pct`
- Type de graphique : Barres groupées

**Q5 — Diplômes par bloc dominant (2022)**
- Filtrer : `annee = 2022`
- Grouper par : `bloc_dominant`
- Résumer : Moyenne de `pct_bac_plus`, `pct_sans_diplome`
- Type de graphique : Barres

**Q6 — Revenus et pauvreté par bloc dominant (2022)**
- Filtrer : `annee = 2022`
- Grouper par : `bloc_dominant`
- Résumer : Médiane de `mediane_revenu_disp`, Moyenne de `taux_pauvrete`
- Type de graphique : Tableau ou barres
- **Note** : `taux_pauvrete` est une valeur **estimée** (non issue de l'INSEE directement). Calculée à partir du revenu médian communal + coefficient de Gini (si disponible), calibrée sur la méthodologie Filosofi INSEE 2020-2022. Précision : ±5%. Couverture : 90% des communes (les 10% restants sont imputés par médiane départementale/nationale).

### Typologie territoire

**Q7 — Bloc dominant par typologie (2022)**
- Filtrer : `annee = 2022`
- Grouper par : `typologie_territoire`, `bloc_dominant`
- Résumer : Nombre de lignes
- Type de graphique : Barres empilées

**Q8 — Caractéristiques socio-économiques par typologie (2022)**
- Filtrer : `annee = 2022`
- Grouper par : `typologie_territoire`
- Résumer : Moyenne de `pct_bac_plus`, `cadres_pct`, `mediane_revenu_disp`
- Type de graphique : Tableau

### Analyse départementale

**Q9 — Top 10 départements Gauche (2022)**
- Filtrer : `annee = 2022`, `bloc_dominant = 'Gauche'`
- Grouper par : `code_dep`
- Résumer : Nombre de lignes
- Trier : Décroissant, limiter à 10
- Type de graphique : Barres

**Q10 — Top 10 départements ExtremeDroite (2022)**
- Filtrer : `annee = 2022`, `bloc_dominant = 'ExtremeDroite'`
- Grouper par : `code_dep`
- Résumer : Nombre de lignes
- Trier : Décroissant, limiter à 10
- Type de graphique : Barres

---

## Table `gold_france.predictions_2022` (predictions modele pour 2022)

### Vue d'ensemble predictive

**Q11 — Predictions 2022 par bloc**
- Resumer : Nombre de lignes
- Grouper par : `bloc_predit`
- Type de graphique : Barres

**Q12 — Communes predites en 2022**
- Colonnes : `code_commune`, `libelle`, `code_dep`, `bloc_predit`, `typologie_territoire`
- Type de graphique : Tableau

**Q13 — Probabilites moyennes par bloc (predit 2022)**
- Resumer : Moyenne de `prob_gauche`, `prob_centre`, `prob_droite`, `prob_extremedroite`
- Type de graphique : Barres

### Analyse par typologie

**Q14 — Predictions 2022 par typologie**
- Grouper par : `typologie_territoire`, `bloc_predit`
- Resumer : Nombre de lignes
- Type de graphique : Barres empilees

**Q15 — Probabilite ExtremeDroite par typologie (predit 2022)**
- Grouper par : `typologie_territoire`
- Resumer : Moyenne de `prob_extremedroite`
- Type de graphique : Barres

### Analyse departementale predictive

**Q16 — Top 20 departements ExtremeDroite (predit 2022)**
- Filtrer : `bloc_predit = 'ExtremeDroite'`
- Grouper par : `code_dep`
- Resumer : Nombre de lignes
- Trier : Decroissant, limiter a 20
- Type de graphique : Barres

**Q17 — Communes mal predites : predit vs reel 2022** *(SQL natif)*
```sql
SELECT
  p.code_commune,
  p.libelle,
  p.code_dep,
  p.bloc_predit,
  fc.bloc_dominant AS bloc_reel,
  p.typologie_territoire
FROM gold_france.predictions_2022 p
JOIN gold_france.features_communes fc
  ON p.code_commune = fc.code_commune
WHERE fc.annee = 2022
  AND p.bloc_predit <> fc.bloc_dominant
ORDER BY p.code_dep, p.libelle
LIMIT 100;
```

---

## Questions croisees `features_communes` et `predictions_2022`

**Q18 — Comparaison reel 2022 vs predit 2022 par departement** *(SQL natif)*
```sql
SELECT 'Reel 2022' AS source, code_dep, bloc_dominant AS bloc, COUNT(*) AS nb
FROM gold_france.features_communes
WHERE annee = 2022
  AND code_dep IN ('59','62','69','13','75','92','93','94','06','33')
GROUP BY code_dep, bloc_dominant
UNION ALL
SELECT 'Predit 2022', p.code_dep, p.bloc_predit, COUNT(*)
FROM gold_france.predictions_2022 p
WHERE code_dep IN ('59','62','69','13','75','92','93','94','06','33')
GROUP BY code_dep, bloc_predit
ORDER BY code_dep, source, nb DESC;
```

**Q19 — Accuracy par bloc : reel vs predit 2022** *(SQL natif)*
```sql
SELECT
  fc.bloc_dominant AS bloc_reel,
  p.bloc_predit,
  COUNT(*) AS nb_communes,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY fc.bloc_dominant), 1) AS pct
FROM gold_france.features_communes fc
JOIN gold_france.predictions_2022 p
  ON fc.code_commune = p.code_commune
WHERE fc.annee = 2022
GROUP BY fc.bloc_dominant, p.bloc_predit
ORDER BY fc.bloc_dominant, nb_communes DESC;
```

**Q20 — Probabilite ExtremeDroite predit pour communes rurales Gauche reel 2022** *(SQL natif)*
```sql
SELECT
  fc.typologie_territoire,
  fc.bloc_dominant AS bloc_reel_2022,
  p.bloc_predit    AS bloc_predit_2022,
  COUNT(*)         AS nb_communes,
  ROUND(AVG(p.prob_extremedroite), 3) AS prob_xd_moy
FROM gold_france.features_communes fc
JOIN gold_france.predictions_2022 p
  ON fc.code_commune = p.code_commune
WHERE fc.annee = 2022
  AND fc.typologie_territoire = 'rural'
  AND fc.bloc_dominant = 'Gauche'
GROUP BY fc.typologie_territoire, fc.bloc_dominant, p.bloc_predit
ORDER BY nb_communes DESC;
```

---

## Dashboards recommandes

### Dashboard 1 — Vue nationale
Questions : Q1, Q2, Q11
Filtre global : `annee`

### Dashboard 2 — Analyse sociodemographique
Questions : Q4, Q5, Q6, Q8
Filtre : `annee = 2022`

### Dashboard 3 — Typologie territoire
Questions : Q7, Q14, Q15
Filtres : `annee`, `typologie_territoire`

### Dashboard 4 — Departements cles
Questions : Q9, Q10, Q16
Filtre : `code_dep` (selection multiple)

### Dashboard 5 — Predictions 2022
Questions : Q12, Q13, Q16

### Dashboard 6 — Comparaison reel vs predit 2022
Questions : Q18, Q19, Q20
Aucun filtre (requetes SQL fixes)
