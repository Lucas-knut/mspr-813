# MSPR-813 : ML Électoral

## Objectif

Modèle ML supervisé pour prédire les tendances électorales (Gauche / Centre / Droite / ExtremeDroite) sur ~35 000 communes de France métropolitaine, horizon 2025-2027.
Startup fictive : **Electio-Analytics**.

---

## Stack

- Python 3.11, pandas, scikit-learn, openpyxl, psycopg2
- Docker + JupyterLab
- PostgreSQL 15 (stockage Silver + Gold)
- Metabase (visualisations)
- **IMPORTANT : pandas uniquement, PAS Spark**

---

## Architecture Medallion (Bronze → Silver → Gold)

```
Bronze (CSV/Excel immuables)
  data/bronze/

Silver (données nettoyées — PostgreSQL)
  schéma silver          → Petite Couronne (75/92/93/94)
  schéma silver_france   → France métropolitaine (depts 01-95 + 2A/2B)

Gold (features ML + prédictions — PostgreSQL)
  schéma gold            → Petite Couronne
  schéma gold_france     → France métropolitaine
```

**Pas de fichiers Parquet locaux.** Tout le Silver et le Gold est dans PostgreSQL.

---

## Connexion PostgreSQL

```python
import psycopg2
conn = psycopg2.connect(
    host="postgres",   # depuis un container Docker
    port=5432,
    database="mspr813",
    user="mspr_user",
    password="mspr_password"
)
```

Host depuis le Mac : `localhost`.

---

## Pipeline Notebooks

### Exploration / EDA

| Notebook | Rôle |
|----------|------|
| `notebooks/01_data_download.ipynb` | Téléchargement toutes les données sources |
| `notebooks/02_exploration.ipynb` | EDA données Bronze |

### Petite Couronne (POC — 144 communes, depts 75/92/93/94)

| Ordre | Notebook | Schémas cibles |
|-------|----------|----------------|
| 1 | `notebooks/petite_couronne/01_etl_bronze_to_postgres.ipynb` | `silver.*` |
| 2 | `notebooks/petite_couronne/02_feature_engineering.ipynb` | `gold.features_communes` |
| 3 | `notebooks/petite_couronne/03_modeling.ipynb` | `gold.predictions_2025_2027` |

### France métropolitaine (~35 000 communes)

| Ordre | Notebook | Schémas cibles |
|-------|----------|----------------|
| 1 | `notebooks/france/01_etl_bronze_to_postgres.ipynb` | `silver_france.*` |
| 2 | `notebooks/france/02_feature_engineering.ipynb` | `gold_france.features_communes` |
| 3 | `notebooks/france/03_modeling.ipynb` | `gold_france.predictions_2025_2027` |

---

## Conventions de Code

### Codes INSEE
Toujours en **string, 5 caractères**, padding zéros :
```python
df['code_insee'] = df['code_insee'].astype(str).str.zfill(5)
```

### Lecture fichiers CSV
Séparateur `;` (format INSEE), sauf `referentiel_communes_2024.csv` (`,`) :
```python
df = pd.read_csv("fichier.csv", sep=";", dtype=str)
```

### Lecture fichiers Excel
Toujours engine `openpyxl` :
```python
df = pd.read_excel("fichier.xlsx", engine="openpyxl")
```

### Périmètre France métropolitaine
Départements 01-95 + 2A/2B. Exclure DOM-TOM et le code 20 (Corse fusionnée).

### Gestion des valeurs manquantes
Imputation par médiane départementale, fallback médiane nationale.

### Configuration dans les notebooks
Inline, pas d'import externe :
```python
import psycopg2

DB_CONFIG = {
    "host": "postgres",
    "port": 5432,
    "database": "mspr813",
    "user": "mspr_user",
    "password": "mspr_password"
}
```

### Exécuter un script Python dans Docker
```bash
docker cp script.py mspr_python:/tmp/script.py
docker exec mspr_python python3 /tmp/script.py
```
Ne jamais utiliser les heredoc (pas de sortie).

---

## Modèle ML

- **Variable cible** : `orientation` — 4 classes : `Gauche`, `Centre`, `Droite`, `ExtremeDroite`
- **Modèle retenu** : GradientBoosting (accuracy 93.3% sur test 2022, France)
- **Features principales** : élections historiques, revenus, gini, taux_pauvrete, CSP, diplômes, naissances/décès, `typologie_territoire`
- **`typologie_territoire`** : `urbain` (≥10 000 hab) / `periurbain` (≥2 000) / `rural` (<2 000)

---

## Règles Générales

- Code commenté en français
- Nommage explicite (tables, colonnes, variables)
- Pas d'emojis dans le code ni les commentaires
- Pipeline ETL idempotent (réexécutable sans effets de bord)
- Scalable : le même code sert pour Petite Couronne et France entière
