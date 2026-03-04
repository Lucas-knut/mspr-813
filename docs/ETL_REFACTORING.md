# Refactoring ETL Pipeline — Mars 2026

## Contexte

La pipeline ETL initiale présentait plusieurs problèmes critiques :

| Problème | Impact |
|----------|--------|
| `silver.revenus` = 0 lignes | Bug de détection de colonne (`Nom géographique GMS` au lieu de `Code géographique`) |
| 124 communes au lieu de 144 | Paris (75056) non éclaté en arrondissements (75101-75120) |
| Datasets Bronze non exploités | emploi, insécurité, immigration, population historique ignorés |
| Modèle ML à 64.5% accuracy | Ne prédit jamais "Centre" (0% recall), features insuffisantes |

## Modifications apportées

### 1. Schéma PostgreSQL (`scripts/init_db.sql`)

**Nouvelles tables Silver :**

| Table | Source | Granularité | Colonnes clés |
|-------|--------|-------------|---------------|
| `silver.population` | `population_historique/DS_RP_SERIE_HISTORIQUE_2022_data.csv` | commune + arrondissement | population, nb_naissances, nb_deces |
| `silver.emploi` | `emploi_chomage/DS_RP_EMPLOI_LR_COMP_2022_data.csv` | commune + arrondissement | actifs, chomeurs, taux_chomage |
| `silver.insecurite` | `insecurite/donnee-dep-*.csv` | département | indicateur, nombre, taux_pour_mille |
| `silver.immigration` | `immigration/IM_119_immigres_par_departement_1968_2021.xlsx` | département | pct_immigres |

**Table modifiée :**
- `silver.revenus` : ancien format (médiane, gini, taux_pauvreté) remplacé par format IRCOM (nb_foyers_fiscaux, revenu_fiscal_ref, impot_net, revenu_moyen_par_foyer, taux_imposition)

**Fix vue :**
- `v_communes_petite_couronne` : codes département corrigés ('092' → '92')

### 2. ETL Bronze → Silver (`notebooks/04_etl_bronze_to_postgres.ipynb`)

**Fix élections (Paris arrondissements) :**
- Pour `code_commune=75056`, extraction du n° arrondissement depuis `code_bv[:2]`
- `code_commune = '751' + arr_num` → 144 communes au lieu de 124

**Revenus réécrit (IRCOM Excel) :**
- Lecture des 5 fichiers `ircom_communes_complet_revenus_{2002,2007,2012,2017,2022}.xlsx`
- Filtre sur lignes "Total", construction `code_commune = Dép(2) + Commune(3)`
- Distribution Paris 75056 → 20 arrondissements proportionnellement à la population

**Population historique (remplace naissances + décès) :**
- Source : `DS_RP_SERIE_HISTORIQUE_2022_data.csv` (format SDMX)
- Mesures POP, BRTH, DEATH pivotées par commune × année
- Années census : 1968-2022, Paris arrondissements natifs

**Nouveaux datasets :**
- **Emploi/chômage** : actifs (EMPSTA_ENQ='1T2'), chômeurs (EMPSTA_ENQ='2'), âge 15-64
- **Insécurité** : criminalité par département (2016+)
- **Immigration** : part d'immigrés par département (1968-2021)

**Fix diplômes :**
- Distribution Paris 75056 → 20 arrondissements via poids population

**Fonctions utilitaires :**
- `get_paris_pop_weights(engine)` : poids population des arrondissements
- `distribute_paris_to_arrondissements(df, weights, cols)` : distribution proportionnelle

### 3. Feature Engineering (`notebooks/05_feature_engineering.ipynb`)

**Gold table étendue (~30 features au lieu de 17) :**

| Catégorie | Features |
|-----------|----------|
| Électorales | pct_gauche/centre/droite/extremedroite, bloc_dominant |
| Démographie | population, nb_naissances, nb_deces, solde_naturel, taux_natalite, taux_mortalite |
| Revenus | revenu_moyen_par_foyer, taux_imposition |
| Emploi | taux_chomage |
| CSP | cadres_pct, ouvriers_pct, employes_pct, artisans_pct, ratio_cadres_ouvriers |
| Diplômes | pct_bac_plus, pct_sans_diplome |
| Insécurité | taux_crimes_mille (département) |
| Immigration | pct_immigres (département) |
| Géographie | is_paris, is_93 |

**Alignement temporel :**

| Élection | Census | IRCOM |
|----------|--------|-------|
| 2002 | 1999 | 2002 |
| 2007 | 2006 | 2007 |
| 2012 | 2011 | 2012 |
| 2017 | 2016 | 2017 |
| 2022 | 2022 | 2022 |

### 4. Modélisation (`notebooks/06_modeling.ipynb`)

**Améliorations :**
- Fusion ExtremeDroite + Droite → 3 classes (seulement 2 samples ED en train)
- Walk-forward validation : Train≤2012→Test 2017, puis Train≤2017→Test 2022
- ~27 features au lieu de 17
- Objectif : accuracy > 70%, recall Centre > 0%

## Vérifications attendues après exécution

- `silver.elections` : 144 communes distinctes
- `silver.population` : 144 communes, années 1968-2022
- `silver.revenus` : > 0 lignes, 5 années × ~144 communes
- `silver.emploi` : 144 communes, années 2011/2016/2022
- `gold.features_communes` : ~720 lignes (144 × 5), taux remplissage > 90%
