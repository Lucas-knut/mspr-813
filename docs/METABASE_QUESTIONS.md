# Questions Metabase — Electio-Analytics

21 questions SQL natif, 6 dashboards. Toutes les questions utilisent le schema
`gold_france` (France metropolitaine, ~34 791 communes).

---

## Recapitulatif

| ID | Nom | Table source | Type graphique | Dashboard |
|----|-----|-------------|---------------|-----------|
| 133 | Q1 - Evolution du score moyen par bloc (2002-2022) | features_communes | Lignes | 1 |
| 136 | Q2 - Communes par bloc dominant et par annee | features_communes | Barres empilees | 1 |
| 130 | Q3 - Repartition des communes par bloc dominant en 2022 (reel) | features_communes | Camembert | 1 |
| 140 | Q4 - Profil CSP moyen par bloc dominant en 2022 | features_communes | Tableau | 2 |
| 139 | Q5 - Niveau de diplome par bloc dominant en 2022 | features_communes | Barres | 2 |
| 141 | Q6 - Revenu et pauvrete par bloc dominant en 2022 | features_communes | Tableau | 2 |
| 148 | Q7 - Communes par bloc et type de territoire en 2022 | features_communes | Barres empilees | 3 |
| 142 | Q8 - Profil socio-economique par type de territoire en 2022 | features_communes | Tableau | 2 |
| 118 | Q9 - Top 15 departements avec le plus de communes Gauche en 2022 | features_communes | Barres | 4 |
| 119 | Q10 - Top 15 departements avec le plus de communes Droite en 2022 | features_communes | Barres | 4 |
| 131 | Q11 - Repartition des predictions 2022 par bloc (modele ML) | predictions_2022 | Camembert | 5 |
| 149 | Q12 - Predictions 2022 par bloc et type de territoire | predictions_2022 | Barres empilees | 3 |
| 143 | Q13 - Probabilite moyenne par bloc selon le modele ML | predictions_2022 | Barres | 5 |
| 147 | Q14 - Probabilite moyenne par bloc et type de territoire (ML) | predictions_2022 | Tableau | 5 |
| 145 | Q15 - Top 15 departements par probabilite Droite moyenne (ML) | predictions_2022 | Barres | 4 |
| 151 | Q16 - Comparaison globale reel 2022 vs predit 2022 | features + predictions | Tableau | 6 |
| 126 | Q17 - Matrice de confusion reel vs predit 2022 | features + predictions | Tableau | 6 |
| 127 | Q18 - Accuracy du modele ML par bloc (reel vs predit 2022) | features + predictions | Tableau | 6 |
| 146 | Q19 - Communes mal predites par le modele en 2022 | features + predictions | Tableau | 6 |
| 152 | Q20 - Historique electoral des communes rurales de Gauche | features_communes | Lignes | 6 |
| 153 | Q21 - Reel vs predit 2022 par bloc (graphique) | features + predictions | Barres groupees | 6 |

---

## SQL des 21 questions

### Q1 - Evolution du score moyen par bloc (2002-2022)

Type : Lignes — axe X : `annee`, metriques : `pct_gauche_moy`, `pct_centre_moy`, `pct_droite_moy`

```sql
SELECT
    annee::text AS annee,
    ROUND(AVG(pct_gauche) * 100, 1)  AS pct_gauche_moy,
    ROUND(AVG(pct_centre) * 100, 1)  AS pct_centre_moy,
    ROUND(AVG(pct_droite) * 100, 1)  AS pct_droite_moy
FROM gold_france.features_communes
GROUP BY annee
ORDER BY annee;
```

---

### Q2 - Communes par bloc dominant et par annee

Type : Barres empilees — axe X : `annee`, serie : `bloc_dominant`, metrique : `pourcentage`

```sql
SELECT
    annee::text AS annee,
    bloc_dominant,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY annee), 1) AS pourcentage
FROM gold_france.features_communes
GROUP BY annee, bloc_dominant
ORDER BY annee, bloc_dominant;
```

---

### Q3 - Repartition des communes par bloc dominant en 2022 (reel)

Type : Camembert — colonnes : `bloc_dominant`, `nb_communes`

```sql
SELECT
    bloc_dominant,
    COUNT(*) AS nb_communes
FROM gold_france.features_communes
WHERE annee = 2022
GROUP BY bloc_dominant
ORDER BY nb_communes DESC;
```

---

### Q4 - Profil CSP moyen par bloc dominant en 2022

Type : Tableau — colonnes : `bloc_dominant`, indicateurs CSP en %

```sql
SELECT
    bloc_dominant,
    ROUND(AVG(cadres_pct) * 100, 1)    AS cadres_pct,
    ROUND(AVG(ouvriers_pct) * 100, 1)  AS ouvriers_pct,
    ROUND(AVG(employes_pct) * 100, 1)  AS employes_pct,
    ROUND(AVG(artisans_pct) * 100, 1)  AS artisans_pct
FROM gold_france.features_communes
WHERE annee = 2022
GROUP BY bloc_dominant
ORDER BY bloc_dominant;
```

---

### Q5 - Niveau de diplome par bloc dominant en 2022

Type : Barres — 1 metrique `pourcentage_habitants`, serie par `indicateur`

```sql
SELECT
    bloc_dominant,
    'Bac+' AS indicateur,
    ROUND(AVG(pct_bac_plus) * 100, 1) AS pourcentage_habitants
FROM gold_france.features_communes
WHERE annee = 2022
GROUP BY bloc_dominant
UNION ALL
SELECT
    bloc_dominant,
    'Sans diplome' AS indicateur,
    ROUND(AVG(pct_sans_diplome) * 100, 1) AS pourcentage_habitants
FROM gold_france.features_communes
WHERE annee = 2022
GROUP BY bloc_dominant
ORDER BY bloc_dominant, indicateur;
```

---

### Q6 - Revenu et pauvrete par bloc dominant en 2022

Type : Tableau — colonnes : `bloc_dominant`, `revenu_median_eur`, `taux_pauvrete_pct`

Note : `taux_pauvrete` est une valeur estimee (non issue directement de l'INSEE), calculee
a partir du revenu median communal + coefficient de Gini, calibree sur la methodologie
Filosofi INSEE 2020-2022. Precision : +/-5%.

```sql
SELECT
    bloc_dominant,
    ROUND(AVG(mediane_revenu_disp)) AS revenu_median_eur,
    ROUND(AVG(taux_pauvrete) * 100, 1) AS taux_pauvrete_pct
FROM gold_france.features_communes
WHERE annee = 2022
GROUP BY bloc_dominant
ORDER BY bloc_dominant;
```

---

### Q7 - Communes par bloc et type de territoire en 2022

Type : Barres empilees — axe X : `territoire`, serie : `bloc_dominant`, metrique : `pourcentage`

```sql
SELECT
    typologie_territoire AS territoire,
    bloc_dominant,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY typologie_territoire), 1) AS pourcentage
FROM gold_france.features_communes
WHERE annee = 2022
GROUP BY typologie_territoire, bloc_dominant
ORDER BY territoire, bloc_dominant;
```

---

### Q8 - Profil socio-economique par type de territoire en 2022

Type : Tableau — colonnes : `territoire`, `pct_bac_plus`, `cadres_pct`, `revenu_median_eur`

```sql
SELECT
    typologie_territoire AS territoire,
    ROUND(AVG(pct_bac_plus) * 100, 1)  AS pct_bac_plus,
    ROUND(AVG(cadres_pct) * 100, 1)    AS cadres_pct,
    ROUND(AVG(mediane_revenu_disp))     AS revenu_median_eur
FROM gold_france.features_communes
WHERE annee = 2022
GROUP BY typologie_territoire
ORDER BY territoire;
```

---

### Q9 - Top 15 departements avec le plus de communes Gauche en 2022

Type : Barres — axe X : `code_dep`, metrique : `nb_communes`

```sql
SELECT
    code_dep,
    COUNT(*) AS nb_communes
FROM gold_france.features_communes
WHERE annee = 2022
  AND bloc_dominant = 'Gauche'
GROUP BY code_dep
ORDER BY nb_communes DESC
LIMIT 15;
```

---

### Q10 - Top 15 departements avec le plus de communes Droite en 2022

Type : Barres — axe X : `code_dep`, metrique : `nb_communes`

```sql
SELECT
    code_dep,
    COUNT(*) AS nb_communes
FROM gold_france.features_communes
WHERE annee = 2022
  AND bloc_dominant = 'Droite'
GROUP BY code_dep
ORDER BY nb_communes DESC
LIMIT 15;
```

---

### Q11 - Repartition des predictions 2022 par bloc (modele ML)

Type : Camembert — colonnes : `bloc_predit`, `nb_communes`

```sql
SELECT
    bloc_predit,
    COUNT(*) AS nb_communes
FROM gold_france.predictions_2022
GROUP BY bloc_predit
ORDER BY nb_communes DESC;
```

---

### Q12 - Predictions 2022 par bloc et type de territoire

Type : Barres empilees — axe X : `territoire`, serie : `bloc_predit`, metrique : `pourcentage`

```sql
SELECT
    typologie_territoire AS territoire,
    bloc_predit,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY typologie_territoire), 1) AS pourcentage
FROM gold_france.predictions_2022
GROUP BY typologie_territoire, bloc_predit
ORDER BY territoire, bloc_predit;
```

---

### Q13 - Probabilite moyenne par bloc selon le modele ML

Type : Barres — axe X : `bloc`, metrique : `probabilite_moy_pct`

```sql
SELECT
    'Gauche'  AS bloc,
    ROUND(AVG(prob_gauche) * 100, 1) AS probabilite_moy_pct
FROM gold_france.predictions_2022
UNION ALL
SELECT
    'Centre'  AS bloc,
    ROUND(AVG(prob_centre) * 100, 1)
FROM gold_france.predictions_2022
UNION ALL
SELECT
    'Droite'  AS bloc,
    ROUND(AVG(prob_droite) * 100, 1)
FROM gold_france.predictions_2022
ORDER BY bloc;
```

---

### Q14 - Probabilite moyenne par bloc et type de territoire (ML)

Type : Tableau — colonnes : `territoire`, `prob_gauche_pct`, `prob_centre_pct`, `prob_droite_pct`

```sql
SELECT
    typologie_territoire AS territoire,
    ROUND(AVG(prob_gauche) * 100, 1) AS prob_gauche_pct,
    ROUND(AVG(prob_centre) * 100, 1) AS prob_centre_pct,
    ROUND(AVG(prob_droite) * 100, 1) AS prob_droite_pct
FROM gold_france.predictions_2022
GROUP BY typologie_territoire
ORDER BY territoire;
```

---

### Q15 - Top 15 departements par probabilite Droite moyenne (ML)

Type : Barres — axe X : `code_dep`, metrique : `prob_droite_moy_pct`

```sql
SELECT
    code_dep,
    ROUND(AVG(prob_droite) * 100, 1) AS prob_droite_moy_pct
FROM gold_france.predictions_2022
GROUP BY code_dep
ORDER BY prob_droite_moy_pct DESC
LIMIT 15;
```

---

### Q16 - Comparaison globale reel 2022 vs predit 2022

Type : Tableau — colonnes : `bloc`, `pourcentage_reel_2022`, `pourcentage_predit_2022`, `ecart`

```sql
WITH reel AS (
    SELECT bloc_dominant AS bloc, COUNT(*) AS nb
    FROM gold_france.features_communes
    WHERE annee = 2022
    GROUP BY bloc_dominant
),
predit AS (
    SELECT bloc_predit AS bloc, COUNT(*) AS nb
    FROM gold_france.predictions_2022
    GROUP BY bloc_predit
),
total_reel   AS (SELECT SUM(nb) AS t FROM reel),
total_predit AS (SELECT SUM(nb) AS t FROM predit)
SELECT
    r.bloc,
    ROUND(r.nb * 100.0 / tr.t, 1) AS pourcentage_reel_2022,
    ROUND(p.nb * 100.0 / tp.t, 1) AS pourcentage_predit_2022,
    ROUND((p.nb * 100.0 / tp.t) - (r.nb * 100.0 / tr.t), 1) AS ecart
FROM reel r
JOIN predit p ON r.bloc = p.bloc
CROSS JOIN total_reel tr
CROSS JOIN total_predit tp
ORDER BY r.bloc;
```

---

### Q17 - Matrice de confusion reel vs predit 2022

Type : Tableau — colonnes : `bloc_reel`, `bloc_predit`, `nb_communes`, `pct_du_bloc_reel`

```sql
SELECT
    fc.bloc_dominant AS bloc_reel,
    p.bloc_predit,
    COUNT(*) AS nb_communes,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY fc.bloc_dominant), 1) AS pct_du_bloc_reel
FROM gold_france.features_communes fc
JOIN gold_france.predictions_2022 p
    ON fc.code_commune = p.code_commune
WHERE fc.annee = 2022
GROUP BY fc.bloc_dominant, p.bloc_predit
ORDER BY fc.bloc_dominant, nb_communes DESC;
```

---

### Q18 - Accuracy du modele ML par bloc (reel vs predit 2022)

Type : Tableau — colonnes : `bloc`, `nb_correct`, `nb_total`, `accuracy_pct`

```sql
SELECT
    fc.bloc_dominant AS bloc,
    SUM(CASE WHEN fc.bloc_dominant = p.bloc_predit THEN 1 ELSE 0 END) AS nb_correct,
    COUNT(*) AS nb_total,
    ROUND(SUM(CASE WHEN fc.bloc_dominant = p.bloc_predit THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS accuracy_pct
FROM gold_france.features_communes fc
JOIN gold_france.predictions_2022 p
    ON fc.code_commune = p.code_commune
WHERE fc.annee = 2022
GROUP BY fc.bloc_dominant
ORDER BY fc.bloc_dominant;
```

---

### Q19 - Communes mal predites par le modele en 2022

Type : Tableau — colonnes : `code_commune`, `libelle`, `code_dep`, `bloc_reel`, `bloc_predit`,
`prob_gauche_pct`, `prob_centre_pct`, `prob_droite_pct`

```sql
SELECT
    p.code_commune,
    p.libelle,
    p.code_dep,
    fc.bloc_dominant                    AS bloc_reel,
    p.bloc_predit,
    ROUND(p.prob_gauche * 100, 1)       AS prob_gauche_pct,
    ROUND(p.prob_centre * 100, 1)       AS prob_centre_pct,
    ROUND(p.prob_droite * 100, 1)       AS prob_droite_pct
FROM gold_france.predictions_2022 p
JOIN gold_france.features_communes fc
    ON p.code_commune = fc.code_commune
WHERE fc.annee = 2022
  AND p.bloc_predit <> fc.bloc_dominant
ORDER BY p.code_dep, p.libelle
LIMIT 500;
```

---

### Q20 - Historique electoral des communes rurales de Gauche

Type : Lignes — axe X : `annee`, serie : `indicateur`, metrique : `score_moyen_pct`

Analyse l'evolution historique des scores dans les communes qui votent Gauche en 2022
et sont de type rural.

```sql
SELECT
    annee::text AS annee,
    'Gauche'  AS indicateur,
    ROUND(AVG(pct_gauche) * 100, 1) AS score_moyen_pct
FROM gold_france.features_communes
WHERE code_commune IN (
    SELECT code_commune
    FROM gold_france.features_communes
    WHERE annee = 2022
      AND bloc_dominant = 'Gauche'
      AND typologie_territoire = 'rural'
)
GROUP BY annee
UNION ALL
SELECT
    annee::text,
    'Centre',
    ROUND(AVG(pct_centre) * 100, 1)
FROM gold_france.features_communes
WHERE code_commune IN (
    SELECT code_commune
    FROM gold_france.features_communes
    WHERE annee = 2022
      AND bloc_dominant = 'Gauche'
      AND typologie_territoire = 'rural'
)
GROUP BY annee
UNION ALL
SELECT
    annee::text,
    'Droite',
    ROUND(AVG(pct_droite) * 100, 1)
FROM gold_france.features_communes
WHERE code_commune IN (
    SELECT code_commune
    FROM gold_france.features_communes
    WHERE annee = 2022
      AND bloc_dominant = 'Gauche'
      AND typologie_territoire = 'rural'
)
GROUP BY annee
ORDER BY annee, indicateur;
```

---

### Q21 - Reel vs predit 2022 par bloc (graphique)

Type : Barres groupees — axe X : `bloc`, serie : `source`, metrique : `pourcentage`

```sql
WITH reel AS (
    SELECT bloc_dominant AS bloc, COUNT(*) AS nb
    FROM gold_france.features_communes
    WHERE annee = 2022
    GROUP BY bloc_dominant
),
predit AS (
    SELECT bloc_predit AS bloc, COUNT(*) AS nb
    FROM gold_france.predictions_2022
    GROUP BY bloc_predit
),
total_reel   AS (SELECT SUM(nb) AS t FROM reel),
total_predit AS (SELECT SUM(nb) AS t FROM predit)
SELECT
    'Reel 2022' AS source,
    r.bloc,
    ROUND(r.nb * 100.0 / tr.t, 1) AS pourcentage
FROM reel r CROSS JOIN total_reel tr
UNION ALL
SELECT
    'Predit 2022' AS source,
    p.bloc,
    ROUND(p.nb * 100.0 / tp.t, 1) AS pourcentage
FROM predit p CROSS JOIN total_predit tp
ORDER BY bloc, source;
```

---

## Dashboards

### Dashboard 1 — Vue nationale
Questions : Q1, Q2, Q3

Apercu de l'evolution des blocs politiques sur la France metropolitaine de 2002 a 2022.

### Dashboard 2 — Analyse sociodemographique
Questions : Q4, Q5, Q6, Q8

Profil socio-economique des communes par bloc dominant et par type de territoire (2022).

### Dashboard 3 — Typologie territoire
Questions : Q7, Q12, Q14

Repartition des blocs et probabilites ML selon la nature du territoire (urbain / periurbain / rural).

### Dashboard 4 — Departements cles
Questions : Q9, Q10, Q15

Analyse departementale : communes Gauche, communes Droite, probabilites ML Droite.

### Dashboard 5 — Predictions 2022
Questions : Q11, Q13, Q14

Vue d'ensemble des predictions du modele ML pour 2022.

### Dashboard 6 — Comparaison reel vs predit 2022
Questions : Q21, Q16, Q17, Q18, Q19, Q20

Validation du modele : comparaison entre les resultats reels 2022 et les predictions.
Inclut la matrice de confusion, l'accuracy par bloc et les communes mal predites.
