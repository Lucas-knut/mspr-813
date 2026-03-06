# MSPR Big Data - Prédiction Électorale

**Projet EPSI - BLOC 3 RNCP35584**
Machine Learning pour prédire les tendances électorales (Gauche / Centre / Droite / ExtremeDroite) sur ~35 000 communes de France métropolitaine, horizon 2025-2027.

---

## Stack Technique

- Python 3.11, pandas, scikit-learn
- PostgreSQL 15 (stockage Silver + Gold)
- Docker + JupyterLab
- Metabase (visualisations)

---

## Démarrage

```bash
docker-compose up -d
```

Accès :
- JupyterLab : http://localhost:8888
- pgAdmin    : http://localhost:5050
- Metabase   : http://localhost:3000

### Initialiser la base de données

Dans pgAdmin ou via psql, exécuter dans l'ordre :

```sql
-- Schémas Petite Couronne
\i scripts/init_db.sql

-- Schémas France métropolitaine
\i scripts/init_db_france.sql
```

### Données Bronze à fournir manuellement

Ces fichiers ne sont pas téléchargeables automatiquement, à placer dans `data/bronze/` :

| Fichier | Emplacement |
|---------|-------------|
| `elections_agregees_1999_2024.csv` | `data/bronze/` |
| `revenus_commune.csv` | `data/bronze/` |
| `referentiel_communes_2024.csv` | `data/bronze/referentiels_cog/` |

Les autres données Bronze (naissances, décès, CSP, diplômes…) peuvent être téléchargées via :

```bash
docker exec mspr_python python3 /app/scripts/download_robust.py
```

---

## Pipeline d'exécution

### Exploration / EDA (optionnel)

| Notebook | Rôle |
|----------|------|
| `notebooks/01_data_download.ipynb` | Téléchargement toutes les données sources (élections, COG, démographie, économie, éducation) |
| `notebooks/02_exploration.ipynb` | Analyse exploratoire des données Bronze |
| `notebooks/03_exploration_nouvelles_donnees.ipynb` | Exploration naissances, décès, CSP |

### Petite Couronne (POC — 144 communes, départements 75/92/93/94)

| Ordre | Notebook | Rôle |
|-------|----------|------|
| 1 | `notebooks/petite_couronne/04_etl_bronze_to_postgres.ipynb` | ETL Bronze → `silver.*` |
| 2 | `notebooks/petite_couronne/05_feature_engineering.ipynb` | Features → `gold.features_communes` |
| 3 | `notebooks/petite_couronne/06_modeling.ipynb` | ML + prédictions → `gold.predictions_2025_2027` |

### France métropolitaine (~35 000 communes)

| Ordre | Notebook | Rôle |
|-------|----------|------|
| 1 | `notebooks/france/04_etl_bronze_to_postgres.ipynb` | ETL Bronze → `silver_france.*` |
| 2 | `notebooks/france/05_feature_engineering.ipynb` | Features → `gold_france.features_communes` |
| 3 | `notebooks/france/06_modeling.ipynb` | ML + prédictions → `gold_france.predictions_2025_2027` |

---

## Résultats

| Périmètre | Modèle retenu | Accuracy | Prédictions |
|-----------|--------------|----------|-------------|
| Petite Couronne | GradientBoosting | — | 372 lignes (124 communes × 3 ans) |
| France métro | GradientBoosting | **93.3%** | 104 349 lignes (~34 783 communes × 3 ans) |

Distribution prédictions 2025 (France) :

| Orientation | Communes |
|------------|---------|
| ExtremeDroite | 23 328 |
| Centre | 6 280 |
| Gauche | 5 165 |
| Droite | 10 |

---

## Architecture Medallion

```
Bronze (CSV/Excel)  →  Silver (PostgreSQL)  →  Gold (PostgreSQL)
  data/bronze/            silver.*                gold.*
                          silver_france.*         gold_france.*
```

Voir `docs/ARCHITECTURE.md` pour le détail.

---

## Documentation

| Fichier | Contenu |
|---------|---------|
| `docs/ARCHITECTURE.md` | Architecture technique, Docker, schémas PostgreSQL, ML |
| `docs/CAHIER_DES_CHARGES.md` | Cahier des charges MSPR |
| `docs/PLAN_FRANCE.md` | Plan détaillé extension France métropolitaine |
| `docs/PLAN_TAUX_PAUVRETE.md` | Méthodologie calcul taux de pauvreté estimé |
| `docs/METABASE_QUESTIONS.md` | Définition des dashboards Metabase |

---

## Credentials PostgreSQL

```
Host (depuis container) : postgres
Host (depuis Mac)       : localhost
Port                    : 5432
Database                : mspr813
User                    : mspr_user
Password                : mspr_password
```
