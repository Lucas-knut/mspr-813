# Architecture du Projet - Big Data Electoral Prediction

**Projet MSPR TPRE813 - EPSI 2026**

---

## Vue d'Ensemble

Pipeline ML complet pour prédire les résultats électoraux 2025-2027 (Gauche / Centre / Droite / ExtremeDroite) sur **~35 000 communes de France métropolitaine**.

---

## Infrastructure Docker

4 containers définis dans `docker-compose.yml` :

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

## Architecture Medallion (Bronze → Silver → Gold)

### Couche Bronze — Sources immuables

Fichiers bruts stockés dans `/app/data/bronze/` (dans le container `mspr_python`) :

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

### Couche Silver — Données nettoyées dans PostgreSQL

Deux périmètres parallèles :

| Schéma | Périmètre | Tables principales |
|--------|-----------|-------------------|
| `silver` | Petite Couronne (75/92/93/94) | `elections`, `revenus`, `csp`, `diplomes`, `demographie`, `referentiel_communes` |
| `silver_france` | France métropolitaine (01-95 + 2A/2B) | `elections`, `revenus`, `naissances_deces`, `csp`, `diplomes`, `referentiel_communes` |

**Règles de nettoyage** :
- Codes INSEE toujours en string, 5 caractères (padding zéros)
- Fichiers CSV : séparateur `;` (format INSEE), sauf `referentiel_communes_2024.csv` (`,`)
- Fichiers Excel : engine `openpyxl`
- Périmètre France métro : départements 01-95 + 2A/2B (hors DOM-TOM)

### Couche Gold — Features ML et prédictions dans PostgreSQL

| Schéma | Table | Contenu | Lignes |
|--------|-------|---------|--------|
| `gold` | `features_communes` | Features Petite Couronne × 5 années | 620 |
| `gold` | `predictions_2025_2027` | Prédictions Petite Couronne | 372 |
| `gold_france` | `features_communes` | Features France × 5 années (2002–2022) | 167 866 |
| `gold_france` | `predictions_2025_2027` | Prédictions France 2025–2027 | 104 349 |

---

## Pipeline de Notebooks

| Notebook | Rôle | Périmètre |
|----------|------|-----------|
| `04_etl_bronze_to_postgres.ipynb` | ETL Bronze → Silver | Petite Couronne |
| `05_feature_engineering.ipynb` | Feature engineering → Gold | Petite Couronne |
| `06_modeling.ipynb` | ML + prédictions | Petite Couronne |
| `04b_etl_france.ipynb` | ETL Bronze → Silver | France métro |
| `05b_feature_engineering_france.ipynb` | Feature engineering → Gold | France métro |
| `06b_modeling_france.ipynb` | ML + prédictions | France métro |

---

## Modèle Machine Learning

**Variable cible** : orientation politique dominante (`Gauche` / `Centre` / `Droite` / `ExtremeDroite`)

**Features principales** :
- Données électorales historiques (2002–2022)
- Revenus médians, Gini, taux de pauvreté estimé
- CSP (catégories socio-professionnelles)
- Diplômes / niveau de formation
- Naissances / décès (dynamique démographique)
- `typologie_territoire` : `urbain` (≥10 000 hab) / `periurbain` (≥2 000) / `rural` (<2 000)

**Résultats (périmètre France) :**

| Modèle | Accuracy (test 2022) |
|--------|---------------------|
| RandomForest | 78.5% |
| **GradientBoosting** | **93.3%** ← retenu |

**Distribution prédictions 2025 :**

| Orientation | Communes |
|------------|---------|
| ExtremeDroite | 23 328 |
| Centre | 6 280 |
| Gauche | 5 165 |
| Droite | 10 |

---

## Gestion des Données Manquantes

**Taux de pauvreté** (non disponible directement par commune INSEE) :
- Estimé à partir du revenu médian disponible et du seuil à 60% (13 686 €/an, médiane nationale 22 810 €/an)
- Niveau 1 (Gini + médiane) : 5 291 communes
- Niveau 2 (médiane seule) : 25 951 communes
- Niveau 3 (imputation médiane départementale puis nationale) : 3 602 communes
- Couverture finale : **100%** sur `gold_france.features_communes`

---

## Visualisation

Metabase (port 3000) connecté à PostgreSQL, 6 dashboards définis dans `docs/METABASE_QUESTIONS.md`.

---

## Scripts utilitaires

| Fichier | Rôle |
|---------|------|
| `scripts/init_db.sql` | Création schémas `silver` + `gold` (Petite Couronne) |
| `scripts/init_db_france.sql` | Création schémas `silver_france` + `gold_france` |
| `scripts/calc_pauvrete.py` | Calcul taux_pauvrete estimé dans `silver_france.revenus` |

---

**Dernière mise à jour** : Mars 2026
