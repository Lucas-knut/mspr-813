# Architecture du Projet - Big Data Electoral Prediction

**Projet MSPR TPRE813 - EPSI 2026**

---

## Vue d'Ensemble

Pipeline ML complet pour predire les resultats electoraux 2022 (Gauche / Centre / Droite) sur **~35 000 communes de France metropolitaine**, avec comparaison aux resultats reels 2022 pour validation du modele. L'extreme droite est fusionnee dans le bloc `Droite`.

**Approche** : entrainement sur les elections 2002/2007/2012, test sur 2017, prediction sur 2022 — les resultats reels 2022 permettent de mesurer la performance reelle du modele.

---

## Infrastructure Docker

4 containers definis dans `docker-compose.yml` :

| Container | Service | Port |
|-----------|---------|------|
| `mspr_python` | JupyterLab + Python 3.11 | 8888 |
| `mspr_postgres` | PostgreSQL 15 | 5432 |
| `mspr_pgadmin` | pgAdmin 4 | 5050 |
| `mspr_metabase` | Metabase | 3000 |

**Credentials PostgreSQL** :
```
Host (depuis container) : postgres
Host (depuis Mac)       : localhost
Port                    : 5432
Database                : mspr813
User                    : mspr_user
Password                : mspr_password
```

---

## Architecture Medallion (Bronze -> Silver -> Gold)

### Couche Bronze — Sources immuables

Fichiers bruts stockes dans `/app/data/bronze/` (dans le container `mspr_python`) :

```
bronze/
├── elections_agregees_1999_2024.csv          (~2.35 GB, sep=;)
├── revenus_commune.csv                        (sep=;)
├── naissances_2008_2024/DS_ETAT_CIVIL_NAIS_COMMUNES_data.csv
├── deces_2008_2024/DS_ETAT_CIVIL_DECES_COMMUNES_data.csv
├── csp_actifs_2554/pop-act2554-csp-cd-6822.xlsx
├── diplomes_formation_2022/base-cc-diplomes-formation-2022.xlsx
└── referentiels_cog/referentiel_communes_2024.csv  (sep=,)
```

### Couche Silver — Donnees nettoyees dans PostgreSQL

Deux perimetres paralleles :

| Schema | Perimetre | Tables principales |
|--------|-----------|-------------------|
| `silver` | Petite Couronne (75/92/93/94) | `elections`, `revenus`, `csp`, `diplomes`, `demographie`, `referentiel_communes` |
| `silver_france` | France metropolitaine (01-95 + 2A/2B) | `elections`, `revenus`, `naissances_deces`, `csp`, `diplomes`, `referentiel_communes` |

**Regles de nettoyage** :
- Codes INSEE toujours en string, 5 caracteres (padding zeros)
- Fichiers CSV : separateur `;` (format INSEE), sauf `referentiel_communes_2024.csv` (`,`)
- Fichiers Excel : engine `openpyxl`
- Perimetre France metro : departements 01-95 + 2A/2B (hors DOM-TOM)

### Couche Gold — Features ML et predictions dans PostgreSQL

| Schema | Table | Contenu | Lignes |
|--------|-------|---------|--------|
| `gold` | `features_communes` | Features Petite Couronne x 5 annees (2002-2022) | 620 |
| `gold` | `predictions_2022` | Predictions Petite Couronne pour 2022 | ~124 |
| `gold_france` | `features_communes` | Features France x 5 annees (2002-2022) | 167 866 |
| `gold_france` | `predictions_2022` | Predictions France pour 2022 | ~34 783 |

---

## Pipeline de Notebooks

### Exploration / EDA

| Notebook | Role |
|----------|------|
| `notebooks/communes/01_data_download.ipynb` | Telechargement des donnees sources |
| `notebooks/communes/02_exploration.ipynb` | EDA donnees Bronze |

### Petite Couronne (POC — 144 communes, depts 75/92/93/94)

| Ordre | Notebook | Schemas cibles |
|-------|----------|----------------|
| 1 | `notebooks/communes/petite_couronne/01_etl_bronze_to_postgres.ipynb` | `silver.*` |
| 2 | `notebooks/communes/petite_couronne/02_feature_engineering.ipynb` | `gold.features_communes` |
| 3 | `notebooks/communes/petite_couronne/03_modeling.ipynb` | `gold.predictions_2022` |

### France metropolitaine (~35 000 communes)

| Ordre | Notebook | Schemas cibles |
|-------|----------|----------------|
| 1 | `notebooks/communes/france/01_etl_bronze_to_postgres.ipynb` | `silver_france.*` |
| 2 | `notebooks/communes/france/02_feature_engineering.ipynb` | `gold_france.features_communes` |
| 3 | `notebooks/communes/france/03_modeling.ipynb` | `gold_france.predictions_2022` |

---

## Modele Machine Learning

**Variable cible** : orientation politique dominante (`Gauche` / `Centre` / `Droite`) — l'extreme droite (FN, RN, etc.) est fusionnee dans `Droite`

**Strategie de validation** :
- Entrainement : elections 2002, 2007, 2012
- Test : elections 2017 (mesure de performance)
- Prediction : 2022 (comparaison avec resultats reels connus)

**Features principales** :
- Donnees electorales historiques (annees precedentes)
- Revenus medians, Gini, taux de pauvrete estime
- CSP (categories socio-professionnelles)
- Diplomes / niveau de formation
- Naissances / deces (dynamique demographique)
- `typologie_territoire` : `urbain` (>=10 000 hab) / `periurbain` (>=2 000) / `rural` (<2 000)

**Resultats (perimetre France) :**

| Modele | Accuracy (test 2017) |
|--------|---------------------|
| RandomForest | ~78% |
| **GradientBoosting** | **93.3%** retenu |

**Comparaison predictions 2022 vs resultats reels 2022** disponible dans Metabase (dashboards "Comparaison reel vs predit 2022").

---

## Gestion des Donnees Manquantes

**Taux de pauvrete** (non disponible directement par commune INSEE) :
- Estime a partir du revenu median disponible et du seuil a 60% (13 686 EUR/an, mediane nationale 22 810 EUR/an)
- Niveau 1 (Gini + mediane) : 5 291 communes
- Niveau 2 (mediane seule) : 25 951 communes
- Niveau 3 (imputation mediane departementale puis nationale) : 3 602 communes
- Couverture finale : **100%** sur `gold_france.features_communes`

---

## Visualisation

Metabase (port 3000) connecte a PostgreSQL, 6 dashboards definis dans `docs/METABASE_QUESTIONS.md`.

---

## Scripts utilitaires

| Fichier | Role |
|---------|------|
| `scripts/init_db.sql` | Creation schemas `silver` + `gold` (Petite Couronne) |
| `scripts/init_db_france.sql` | Creation schemas `silver_france` + `gold_france` |
| `scripts/calc_pauvrete.py` | Calcul taux_pauvrete estime dans `silver_france.revenus` |
| `scripts/setup_metabase.py` | Creation questions et dashboards dans Metabase |

---

**Derniere mise a jour** : Avril 2026
