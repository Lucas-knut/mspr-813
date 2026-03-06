# Refactoring ETL Pipeline - Branche `fix/etl-pipeline-refactoring`

## Contexte

La pipeline ETL initiale presentait plusieurs problemes critiques :

| Probleme | Impact |
|----------|--------|
| `silver.revenus` = 0 lignes | Bug de detection de colonne dans le parsing Excel IRCOM |
| 124 communes au lieu de 144 | Paris (75056) non eclate en arrondissements (75101-75120) |
| Datasets Bronze non exploites | emploi, insecurite, immigration, population historique ignores |
| Modele ML a 64.5% accuracy | Ne predit jamais "Centre" (0% recall), features insuffisantes |

---

## Commits de la branche

### 1. `c197b6c` - Infrastructure initiale
- Mise en place de l'architecture de base

### 2. `0e31305` - Schema Metabase
- Ajout du schema Metabase pour le stockage de metadonnees dans `init_db.sql`

### 3. `eba2962` - Merge PR #1 (06-modeling)
- Integration du notebook de modelisation initial

### 4. `1820c9d` - Extension schema PostgreSQL
Ajout de nouvelles tables Silver dans `scripts/init_db.sql` :

| Table | Source | Granularite | Colonnes cles |
|-------|--------|-------------|---------------|
| `silver.population` | DS_RP_SERIE_HISTORIQUE_2022 | commune | population, nb_naissances, nb_deces |
| `silver.emploi` | DS_RP_EMPLOI_LR_COMP_2022 | commune | actifs, chomeurs, taux_chomage |
| `silver.insecurite` | donnee-dep-*.csv | departement | indicateur, nombre, taux_pour_mille |
| `silver.immigration` | IM_119_immigres_par_departement | departement | pct_immigres |

Modification de `silver.revenus` : ancien format (mediane, gini, taux_pauvrete) remplace par format IRCOM (nb_foyers_fiscaux, revenu_fiscal_ref, impot_net, revenu_moyen_par_foyer, taux_imposition).

Fix vue `v_communes_petite_couronne` : codes departement corriges ('092' -> '92').

### 5. `5963ac8` - Reecriture ETL Bronze -> Silver

**Fix elections (Paris arrondissements) :**
- Pour `code_commune=75056`, extraction du numero arrondissement depuis `code_bv[:2]`
- `code_commune = '751' + arr_num` -> 144 communes au lieu de 124

**Revenus reecrit (IRCOM Excel) :**
- Lecture des 5 fichiers `ircom_communes_complet_revenus_{2002..2022}.xlsx`
- Filtre sur lignes "Total", construction `code_commune = Dep(2) + Commune(3)`
- Distribution Paris 75056 -> 20 arrondissements proportionnellement a la population

**Population historique (remplace naissances + deces) :**
- Source : `DS_RP_SERIE_HISTORIQUE_2022_data.csv` (format SDMX)
- Mesures POP, BRTH, DEATH pivotees par commune x annee
- Annees census : 1968, 1975, 1982, 1990, 1999, 2006, 2011, 2016, 2022

**Nouveaux datasets :**
- Emploi/chomage : actifs, chomeurs, age 15-64 ans
- Insecurite : criminalite par departement (2016+)
- Immigration : part d'immigres par departement (1968-2021)

**Fonctions utilitaires :**
- `get_paris_pop_weights(engine)` : poids population des arrondissements parisiens
- `distribute_paris_to_arrondissements(df, weights, cols)` : distribution proportionnelle

### 6. `d434115` - Extension Gold table (17 -> 30 features)

| Categorie | Features |
|-----------|----------|
| Electorales | pct_gauche, pct_centre, pct_droite, pct_extremedroite, bloc_dominant |
| Demographie | population, nb_naissances, nb_deces, solde_naturel, taux_natalite, taux_mortalite |
| Revenus | revenu_moyen_par_foyer, taux_imposition |
| Emploi | taux_chomage |
| CSP | cadres_pct, ouvriers_pct, employes_pct, artisans_pct, ratio_cadres_ouvriers |
| Diplomes | pct_bac_plus, pct_sans_diplome |
| Insecurite | taux_crimes_mille (departement) |
| Immigration | pct_immigres (departement) |
| Geographie | is_paris, is_93 |

Alignement temporel elections -> census -> IRCOM :

| Election | Census | IRCOM |
|----------|--------|-------|
| 2002 | 1999 | 2002 |
| 2007 | 2006 | 2007 |
| 2012 | 2011 | 2012 |
| 2017 | 2016 | 2017 |
| 2022 | 2022 | 2022 |

### 7. `1326741` - Amelioration modele ML

- Fusion ExtremeDroite + Droite -> 3 classes (seulement 2 samples ED en train)
- Walk-forward validation : Train<=2012 -> Test 2017, puis Train<=2017 -> Test 2022
- ~27 features au lieu de 17
- Meilleur modele : GradientBoosting (accuracy=0.664)
- Predictions 2025-2027 generees (432 lignes = 144 communes x 3 annees)

### 8. `b9f4877` - Documentation ETL

### 9. `80bf14c` - Scripts generateurs de notebooks

### 10. Fix bugs ETL Bronze -> Postgres (non commite avant ce commit)

3 bugs corriges dans `04_etl_bronze_to_postgres.ipynb` :

**Bug 1 - Revenus IRCOM : parsing Excel casse**
- Probleme : `skiprows=5` sautait la ligne d'en-tete (position variable selon l'annee)
- Probleme : colonne `Dep.` fait 3 chiffres (ex: `750` pour Paris, `922` pour 92) -> `code_commune` de 6 chars au lieu de 5, rejet par PostgreSQL `character(5)`
- Probleme : filtre `== 'Total'` ne matchait pas `'TOTAL'` (fichier 2017)
- Fix : detection automatique de la ligne d'en-tete, `Dep.[:2]` pour le departement, filtre case-insensitive, fallback sur l'ancien nommage de fichiers (`ircom-communes-revenus-{year}.xlsx`)

**Bug 2 - Emploi : cast Int64 echoue**
- Probleme : `OBS_VALUE` contient des decimales (ex: `616.01967`), cast direct `astype('Int64')` echoue
- Fix : ajout `.round(0)` avant le cast

**Bug 3 - Immigration : mauvaise detection d'en-tete**
- Probleme : recherche de `'partement'` matchait la row 2 (titre du graphique "Part d'immigres dans la population des departements") au lieu de la row 43 (vraie en-tete)
- Fix : chercher `'Code departement'` comme valeur exacte dans la row

---

## Etat des donnees en base (apres execution)

### Silver Layer

| Table | Lignes | Communes/Deps | Annees | Status |
|-------|--------|---------------|--------|--------|
| referentiel_communes | 144 | 4 deps (75:21, 92:36, 93:40, 94:47) | - | OK |
| elections | 1,517,115 | 144 communes | 1999-2024 | OK |
| population | 1,287 | 143 communes | 1968-2022 | OK |
| revenus | 695 | 163 communes | 2002-2022 | Attention |
| emploi | 429 | 143 communes | 2011-2022 | Attention |
| csp | 143 | 143 communes | 2022 | OK |
| diplomes | 142 | 142 communes | 2022 | OK |
| insecurite | 720 | 4 deps | 2016-2025 | OK |
| immigration | 16 | 4 deps | 1968-2021 | OK |
| naissances | 0 | - | - | Remplace par population |
| deces | 0 | - | - | Remplace par population |

### Gold Layer

| Table | Lignes | Detail |
|-------|--------|--------|
| features_communes | 716 | 144 communes x 5 annees (2002-2022), 30 features |
| predictions_2025_2027 | 432 | 144 communes x 3 annees predites |

### Controles de qualite effectues

- **0 doublons** sur population, revenus, emploi
- **0 valeurs aberrantes** sur revenus (pas de negatifs, taux imposition entre 0 et 1)
- **0 nulls** sur colonnes critiques (code_commune, annee) dans toutes les tables
- **Elections** : granularite bureau de vote (55,338 combinaisons uniques commune x election x candidat)
- **Taux de chomage** : plages coherentes (4-26% en 2011/2016)
- **CSP et diplomes** : 0 nulls sur toutes les colonnes numeriques
- **Immigration** : donnees coherentes (ex: Seine-Saint-Denis 31.2% en 2021, le plus eleve)

---

## Points d'attention a retravailler

### P1 - Critique

**Emploi 2022 : chomeurs = NULL pour les 143 communes**
- `actifs` est renseigne, mais `chomeurs` est NULL partout en 2022
- Le fichier source INSEE `DS_RP_EMPLOI_LR_COMP_2022_data.csv` ne contient pas de lignes `EMPSTA_ENQ='2'` (chomeurs) pour 2022
- Impact : `taux_chomage` NULL en 2022 dans la Gold table -> le modele perd cette feature pour l'annee la plus recente
- Action : verifier si une version plus recente du fichier INSEE est disponible, ou utiliser les donnees Pole Emploi / DARES comme alternative

### P2 - Important

**Revenus 2012 : 123 communes au lieu de 143 (arrondissements Paris manquants)**
- Le fichier IRCOM 2012 contient Paris en `75056` global, mais le code `Dep.[:2]` produit `'75'` et `Commune` = `'056'` -> `code_commune = '75056'`
- La distribution vers les arrondissements ne fonctionne pas car la table population n'est pas encore remplie au moment du traitement (la fonction `get_paris_pop_weights` renvoie un dict vide)
- Impact : 20 arrondissements parisiens sans donnees revenus en 2012
- Action : reordonner le traitement (population avant revenus) ou pre-charger les poids

**Revenus : 163 communes distinctes au lieu de 144**
- Certains codes commune dans les fichiers IRCOM ne correspondent pas au referentiel COG 2024
- Probablement des communes fusionnees ou des codes temporaires
- Impact : 19 codes commune "orphelins" sans correspondance dans le referentiel
- Action : ajouter un filtre `code_commune IN (SELECT code_insee FROM silver.referentiel_communes)` avant l'insertion

### P3 - Mineur

**Elections : nuance_liste NULL pour 14% des lignes**
- Presidentielles : 40% de NULL, Europeennes : 20% de NULL
- C'est normal : le fichier source n'a pas de nuance pour tous les candidats
- Impact : le mapping nuance -> bloc politique peut rater certaines lignes
- Action : enrichir le mapping de nuances ou utiliser le nom du candidat comme fallback

**Tables naissances et deces vides**
- Ces tables ne sont plus alimentees car remplacees par les colonnes `nb_naissances` et `nb_deces` dans `silver.population`
- Action : supprimer ces tables du schema `init_db.sql` pour eviter la confusion

**Modele ML : accuracy 66.4%**
- GradientBoosting est le meilleur modele, mais l'accuracy reste modeste
- La classe "Centre" est difficile a predire (peu de samples historiques)
- Les predictions 2025-2027 sont quasi-unanimement "Gauche" (142/144 communes)
- Action : envisager d'ajouter des features (donnees de sondages, resultats precedents par bureau de vote, densite de population) ou de passer en regression (predire le % de voix plutot que le bloc dominant)

---

## Structure des fichiers modifies

```
scripts/
  init_db.sql                       # Schema PostgreSQL (Silver + Gold)
  generate_etl_notebook.py          # Generateur notebook ETL
  generate_fe_notebook.py           # Generateur notebook Feature Engineering
  generate_ml_notebook.py           # Generateur notebook Modeling

notebooks/
  04_etl_bronze_to_postgres.ipynb   # ETL Bronze -> Silver (PostgreSQL)
  05_feature_engineering.ipynb      # Silver -> Gold (features ML)
  06_modeling.ipynb                 # Entrainement + predictions

docker-compose.yml                  # Port Postgres 5433 (evite conflit local)
```

## Comment re-executer

```bash
# 1. Demarrer les containers
docker compose up -d

# 2. Executer les notebooks dans l'ordre
docker exec mspr_python jupyter nbconvert --to notebook --execute \
  /app/notebooks/04_etl_bronze_to_postgres.ipynb \
  --ExecutePreprocessor.timeout=600

docker exec mspr_python jupyter nbconvert --to notebook --execute \
  /app/notebooks/05_feature_engineering.ipynb \
  --ExecutePreprocessor.timeout=300

docker exec mspr_python jupyter nbconvert --to notebook --execute \
  /app/notebooks/06_modeling.ipynb \
  --ExecutePreprocessor.timeout=600

# 3. Verifier en base
docker exec mspr_postgres psql -U mspr_user -d mspr813 -c \
  "SELECT table_name FROM information_schema.tables WHERE table_schema='silver';"
```
