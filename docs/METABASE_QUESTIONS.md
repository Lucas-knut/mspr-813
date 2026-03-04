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

## Table `gold_france.predictions_2025_2027` (prédictions futures)

### Vue d'ensemble prédictive

**Q11 — Évolution prédite 2025–2027**
- Résumer : Nombre de lignes
- Grouper par : `annee`, `bloc_predit`
- Type de graphique : Barres empilées ou lignes

**Q12 — Communes prédites en 2027**
- Filtrer : `annee = 2027`
- Colonnes : `code_commune`, `libelle`, `code_dep`, `bloc_predit`, `typologie_territoire`
- Type de graphique : Tableau

**Q13 — Probabilités moyennes par bloc en 2027**
- Filtrer : `annee = 2027`
- Résumer : Moyenne de `prob_gauche`, `prob_centre`, `prob_droite`, `prob_extremedroite`
- Type de graphique : Barres

### Analyse par typologie

**Q14 — Prédictions 2027 par typologie**
- Filtrer : `annee = 2027`
- Grouper par : `typologie_territoire`, `bloc_predit`
- Résumer : Nombre de lignes
- Type de graphique : Barres empilées

**Q15 — Probabilité ExtremeDroite par typologie (2027)**
- Filtrer : `annee = 2027`
- Grouper par : `typologie_territoire`
- Résumer : Moyenne de `prob_extremedroite`
- Type de graphique : Barres

### Analyse départementale prédictive

**Q16 — Top 20 départements ExtremeDroite (2027)**
- Filtrer : `annee = 2027`, `bloc_predit = 'ExtremeDroite'`
- Grouper par : `code_dep`
- Résumer : Nombre de lignes
- Trier : Décroissant, limiter à 20
- Type de graphique : Barres

**Q17 — Départements bascule ExtremeDroite → Centre (2025→2027)** *(SQL natif)*
```sql
SELECT p25.code_dep, COUNT(*) AS nb_bascules
FROM gold_france.predictions_2025_2027 p25
JOIN gold_france.predictions_2025_2027 p27
  ON p25.code_commune = p27.code_commune
WHERE p25.annee = 2025 AND p25.bloc_predit = 'ExtremeDroite'
  AND p27.annee = 2027 AND p27.bloc_predit = 'Centre'
GROUP BY p25.code_dep
ORDER BY nb_bascules DESC
LIMIT 10;
```

---

## Questions croisées `features_communes` ⇄ `predictions_2025_2027`

**Q18 — Évolution 2022 → 2027 par département (10 plus grands)** *(SQL natif)*
```sql
SELECT 'Réel 2022' AS source, code_dep, bloc_dominant AS bloc, COUNT(*) AS nb
FROM gold_france.features_communes
WHERE annee = 2022
  AND code_dep IN ('59','62','69','13','75','92','93','94','06','33')
GROUP BY code_dep, bloc_dominant
UNION ALL
SELECT 'Prédit 2027', code_dep, bloc_predit, COUNT(*)
FROM gold_france.predictions_2025_2027
WHERE annee = 2027
  AND code_dep IN ('59','62','69','13','75','92','93','94','06','33')
GROUP BY code_dep, bloc_predit
ORDER BY code_dep, source, nb DESC;
```

**Q19 — Devenir des communes ExtremeDroite 2022 en 2027** *(SQL natif)*
```sql
SELECT
  p27.bloc_predit,
  COUNT(*) AS nb_communes,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM gold_france.features_communes fc
JOIN gold_france.predictions_2025_2027 p27
  ON fc.code_commune = p27.code_commune
WHERE fc.annee = 2022 AND fc.bloc_dominant = 'ExtremeDroite'
  AND p27.annee = 2027
GROUP BY p27.bloc_predit
ORDER BY nb_communes DESC;
```

**Q20 — Probabilité ExtremeDroite en 2027 pour les communes rurales Gauche en 2022** *(SQL natif)*
```sql
SELECT
  fc.typologie_territoire,
  fc.bloc_dominant AS bloc_2022,
  p27.bloc_predit  AS bloc_2027,
  COUNT(*)         AS nb_communes,
  ROUND(AVG(p27.prob_extremedroite), 3) AS prob_xd_moy
FROM gold_france.features_communes fc
JOIN gold_france.predictions_2025_2027 p27
  ON fc.code_commune = p27.code_commune
WHERE fc.annee = 2022
  AND p27.annee = 2027
  AND fc.typologie_territoire = 'rural'
  AND fc.bloc_dominant = 'Gauche'
GROUP BY fc.typologie_territoire, fc.bloc_dominant, p27.bloc_predit
ORDER BY nb_communes DESC;
```

---

## Dashboards recommandés

### Dashboard 1 — Vue nationale
Questions : Q1, Q2, Q11
Filtre global : `annee`

### Dashboard 2 — Analyse sociodémographique
Questions : Q4, Q5, Q6, Q8
Filtre : `annee = 2022`

### Dashboard 3 — Typologie territoire
Questions : Q7, Q14, Q15
Filtres : `annee`, `typologie_territoire`

### Dashboard 4 — Départements clés
Questions : Q9, Q10, Q16, Q17
Filtre : `code_dep` (sélection multiple)

### Dashboard 5 — Prédictions 2027
Questions : Q12, Q13, Q16
Fixé sur `annee = 2027`

### Dashboard 6 — Comparaison 2022 vs 2027
Questions : Q18, Q19, Q20
Aucun filtre (requêtes SQL fixes)
