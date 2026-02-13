# Architecture des Données - Medallion (Bronze/Silver/Gold)

**Projet MSPR TPRE813 - EPSI 2026**

## Vue d'Ensemble

Ce projet adopte l'**architecture Medallion** (aussi appelée Bronze/Silver/Gold), standard de l'industrie en Data Engineering moderne, popularisée par Databricks et largement utilisée dans les plateformes Big Data (Snowflake, Delta Lake, Azure Synapse).

### Principes Fondamentaux

```
🥉 Bronze → 🥈 Silver → 🥇 Gold
(Source)   (Nettoyé)   (Agrégé/ML)
```

Chaque couche a une **responsabilité unique** et des **garanties de qualité** spécifiques, permettant une traçabilité complète du pipeline de données.

---

## 🥉 Couche Bronze - Données Brutes

**Localisation** : `data/bronze/`

**Rôle** : Zone de landing pour données sources, **immuables après téléchargement**

### Caractéristiques

- **Format** : Original (CSV, XLSX, JSON, ZIP)
- **Transformations** : AUCUNE - Données "as-is"
- **Qualité** : Aucune garantie (peut contenir erreurs, doublons, valeurs manquantes)
- **Accès** : Read-only après téléchargement initial
- **Traçabilité** : URL source + date de téléchargement documentées

### Fichiers Présents

| Fichier | Taille | Source | Description | Téléchargé |
|---------|--------|--------|-------------|------------|
| `elections_agregees_1999_2024.csv` | 2.2 GB | data.gouv.fr | Résultats élections 1999-2024 | 10/02/2026 |
| `revenus_commune.csv` | 4.8 MB | INSEE | Revenus fiscaux par commune | 10/02/2026 |
| `referentiel_communes.csv` | 2.5 MB | INSEE | Référentiel 37.5K communes France | 10/02/2026 |
| `population_historique_1968_2022/` | 43.6 MB | INSEE | Population par âge 1968-2022 | 10/02/2026 |
| `diplomes_formation_2022/` | 66 MB | INSEE | Niveaux diplômes par commune | 10/02/2026 |
| `csp_actifs_2554/` | 28.5 MB | INSEE | CSP actifs 25-54 ans | 10/02/2026 |

**Total Bronze** : ~2.36 GB

### Notebook Responsable

- **`01_data_download.ipynb`** : Téléchargement depuis sources publiques

### Règles de Gestion Bronze

- ❌ **JAMAIS modifier** un fichier Bronze après téléchargement
- ✅ Re-télécharger si source mise à jour (versionner: `elections_2024.csv`, `elections_2025.csv`)
- ✅ Garder ZIP originaux si nécessaire pour traçabilité
- ✅ Documenter métadonnées : URL source, date téléchargement, hash MD5

---

## 🥈 Couche Silver - Données Nettoyées

**Localisation** : `data/silver/`

**Rôle** : Données validées, typées, converties en format optimisé Parquet

### Caractéristiques

- **Format** : Parquet (compression snappy, engine pyarrow)
- **Transformations** : Parsing, typage, filtrage, déduplication
- **Qualité** : Données validées, tests qualité passés
- **Accès** : Read/Write (peut être régénéré depuis Bronze)
- **Performance** : 10-100x plus rapide que CSV

### Transformations Appliquées

1. ✅ **Parsing correct** :
   - Séparateurs CSV (`;` pour fichiers français)
   - Skiprows pour métadonnées INSEE (lignes 0-4)
   
2. ✅ **Types de données cohérents** :
   ```python
   dtype={
       'code_commune': str,      # Codes INSEE en string (garder leading zeros)
       'code_departement': str,
       'annee': int,
       'population': int,
       'revenus_median': float
   }
   ```

3. ✅ **Filtrage géographique** :
   - Petite Couronne : 144 communes (75, 92, 93, 94)
   - Suppression codes spéciaux (COM, arrondissements municipaux)

4. ✅ **Conversion Parquet** :
   - Compression `snappy` (bon compromis vitesse/taille)
   - Engine `pyarrow` (performance optimale)

5. ✅ **Qualité données** :
   - Suppression doublons
   - Identification valeurs manquantes
   - Détection valeurs aberrantes (outliers)

6. ✅ **Normalisation colonnes** :
   - Noms colonnes en `snake_case`
   - Suppression accents et caractères spéciaux
   - Colonnes cohérentes entre datasets

### Fichiers Attendus

| Fichier | Description | Lignes | Colonnes | Taille |
|---------|-------------|--------|----------|--------|
| `referentiel_petite_couronne.parquet` | 144 communes PC | 144 | 10 | 4.8 KB |
| `elections_petite_couronne.parquet` | Élections filtrées 75/92/93/94 | ~2M | 18 | ~40 MB |
| `revenus_petite_couronne.parquet` | Revenus 144 communes | 144 | 15 | ~15 KB |
| `population_petite_couronne.parquet` | Population par âge | 144 | 50 | ~50 KB |
| `diplomes_petite_couronne.parquet` | Niveaux diplômes | 144 | 60 | ~60 KB |
| `csp_petite_couronne.parquet` | CSP actifs | 144 | 30 | ~30 KB |

**Total Silver** : ~50 MB (compression 98% vs Bronze !)

### Notebooks Responsables

- **`02_exploration.ipynb`** : Exploration initiale + premiers exports Silver
- **`03_etl.ipynb`** : ETL complet Bronze → Silver

### Règles de Gestion Silver

- ✅ Peut être **régénéré depuis Bronze** à tout moment (idempotence)
- ✅ Ajouter métadonnées Parquet :
  ```python
  df.to_parquet(
      path,
      metadata={
          'source': 'elections_agregees_1999_2024.csv',
          'transformation_date': '2026-02-13',
          'code_version': 'v1.2.3'
      }
  )
  ```
- ✅ Tests qualité obligatoires :
  - Valeurs manquantes < 5% par colonne
  - Pas de doublons sur clé primaire (code_commune)
  - Types de données cohérents
- ✅ Documenter transformations appliquées (notebook + commentaires)

---

## 🥇 Couche Gold - Données Agrégées / ML-Ready

**Localisation** : `data/gold/`

**Rôle** : Tables finales pour analyse métier, visualisations et Machine Learning

### Caractéristiques

- **Format** : Parquet + JSON (métriques) + CSV (exports client)
- **Transformations** : Jointures, features engineering, agrégations temporelles
- **Qualité** : Business-ready, documenté, versionné
- **Accès** : Read/Write (outputs ML, prédictions)
- **Usage** : Dashboards, modèles ML, livrables client

### Transformations Appliquées

1. ✅ **Jointures multi-sources** :
   ```
   referentiel_petite_couronne
   ├── LEFT JOIN elections (sur code_commune)
   ├── LEFT JOIN revenus (sur code_commune)
   ├── LEFT JOIN population (sur code_commune)
   ├── LEFT JOIN diplomes (sur code_commune)
   └── LEFT JOIN csp (sur code_commune)
   = dataset_ml_complet
   ```

2. ✅ **Features Engineering** :
   - **Ratios** : `taux_chomage = chomeurs / actifs`
   - **Tendances** : Évolution population 2015-2022 (croissance/déclin)
   - **Indicateurs composites** : Indice de précarité, diversité socio-économique
   - **Variables catégorielles** : Encoding one-hot (parti politique dominant)

3. ✅ **Agrégations temporelles** :
   - Moyennes glissantes 3 ans (lissage fluctuations)
   - Évolutions annuelles (taux de croissance)
   - Lag features (valeurs année N-1, N-2, N-3)

4. ✅ **Dataset ML** :
   - Split train/test (80/20)
   - Normalisation features (StandardScaler)
   - Gestion valeurs manquantes (imputation médiane)

5. ✅ **Prédictions & Résultats** :
   - Prévisions électorales 2027
   - Scores importance features
   - Métriques performance (RMSE, R², MAE)

### Fichiers Attendus

| Fichier | Description | Usage | Format |
|---------|-------------|-------|--------|
| `dataset_ml_complet.parquet` | Features + target jointurées | Training ML | Parquet |
| `dataset_train.parquet` | 80% données (training set) | Entraînement modèle | Parquet |
| `dataset_test.parquet` | 20% données (validation) | Évaluation modèle | Parquet |
| `predictions_2027.parquet` | Prévisions électorales 2027 | Livrable client | Parquet |
| `features_importance.parquet` | Importance variables | Interprétabilité | Parquet |
| `metriques_modele.json` | Scores (RMSE, R², MAE) | Reporting | JSON |
| `export_client_2027.csv` | Prédictions format CSV | Livrable client | CSV |

**Total Gold** : ~10 MB

### Notebooks Responsables

- **`04_features.ipynb`** : Features engineering Silver → Gold
- **`05_modeling.ipynb`** : Entraînement modèles ML
- **`06_predictions.ipynb`** : Génération prévisions 2027

### Règles de Gestion Gold

- ✅ Documenter **chaque feature** engineerée :
  ```python
  # Feature: Indice de précarité (0-100)
  # Formule: (taux_chomage*0.4 + taux_pauvrete*0.4 + taux_sans_diplome*0.2) * 100
  # Source: INSEE + méthodologie interne
  df['indice_precarite'] = (
      df['taux_chomage'] * 0.4 + 
      df['taux_pauvrete'] * 0.4 + 
      df['taux_sans_diplome'] * 0.2
  ) * 100
  ```

- ✅ **Versionner modèles ML** :
  ```
  models/
  ├── model_v1_20260213.pkl  # Random Forest baseline
  ├── model_v2_20260220.pkl  # XGBoost optimisé
  └── model_v3_20260227.pkl  # Ensemble voting
  ```

- ✅ **Exporter métriques** pour chaque run :
  ```json
  {
    "model": "RandomForestRegressor",
    "date": "2026-02-13",
    "hyperparameters": {"n_estimators": 100, "max_depth": 10},
    "metrics": {
      "rmse": 0.082,
      "r2": 0.76,
      "mae": 0.061
    }
  }
  ```

- ✅ **Traçabilité complète** : Quel modèle a généré quelles prédictions ?

---

## Flux de Données Complet

```
┌──────────────────────────────────────────────────────────┐
│              01_data_download.ipynb                      │
│                                                          │
│  data.gouv.fr ──┐                                       │
│  INSEE.fr ──────┼──► 🥉 data/bronze/ (2.36 GB)         │
│  Sources API ───┘     • Format original (CSV, XLSX)    │
│                       • Données immuables                │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│      02_exploration.ipynb + 03_etl.ipynb                 │
│                                                          │
│  Parsing ──────┐                                        │
│  Typage ───────┼──► 🥈 data/silver/ (~50 MB)           │
│  Filtrage ─────┘     • Format Parquet optimisé         │
│  Déduplication       • 144 communes Petite Couronne     │
│  Validation          • Types validés, qualité contrôlée │
│                                                          │
│  Fichiers générés:                                       │
│  • referentiel_petite_couronne.parquet                   │
│  • elections_petite_couronne.parquet                     │
│  • revenus/population/diplomes/csp.parquet               │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│  04_features + 05_modeling + 06_predictions              │
│                                                          │
│  Jointures ───────┐                                     │
│  Features ────────┼──► 🥇 data/gold/ (~10 MB)          │
│  ML Training ─────┘     • Tables business-ready        │
│  Prédictions            • Features ML engineerées       │
│                         • Résultats & métriques         │
│                                                          │
│  Fichiers générés:                                       │
│  • dataset_ml_complet.parquet                            │
│  • dataset_train/test.parquet                            │
│  • predictions_2027.parquet                              │
│  • metriques_modele.json                                 │
└──────────────────────────────────────────────────────────┘
```

---

## Avantages Architecture Medallion

### ✅ Traçabilité Complète

- **Bronze** : Source de vérité immuable (audit trail)
- **Silver** : Transformations documentées et reproductibles
- **Gold** : Résultats traçables jusqu'à la source

**Exemple** : Une prédiction électorale anormale peut être retracée :
```
Prédiction Gold → Feature Silver → Donnée Bronze → URL source INSEE
```

### ✅ Séparation des Responsabilités

Chaque couche a un **rôle unique** :
- **Bronze** : Ingestion simple, pas de logique métier
- **Silver** : Qualité données (Data Quality checks)
- **Gold** : Business logic et ML

**Avantage** : Bugs isolés, debugging facilité, maintenabilité accrue

### ✅ Performance Optimale

| Couche | Format | Taille | Temps lecture (100K lignes) |
|--------|--------|--------|----------------------------|
| Bronze | CSV | 2.36 GB | 8-12 secondes |
| Silver | Parquet | 50 MB | 0.3-0.5 secondes |
| Gold | Parquet | 10 MB | 0.1-0.2 secondes |

**Compression** : Bronze 2.36 GB → Silver 50 MB → Gold 10 MB (99.6% réduction !)

### ✅ Scalabilité

Même code fonctionne pour :
- **POC** : 144 communes Petite Couronne
- **Production** : 35 000 communes France entière

**Techniques** :
- Partitionnement Parquet (par département, région)
- Chunked reading (traitement par blocs)
- Dask/Spark si volume > 100 GB

### ✅ Reproductibilité

**Pipeline linéaire** : Bronze → Silver → Gold

Exécution dans l'ordre **garantit résultats identiques** :
```bash
# Re-créer tout le pipeline
jupyter nbconvert --execute 01_data_download.ipynb
jupyter nbconvert --execute 02_exploration.ipynb
jupyter nbconvert --execute 03_etl.ipynb
jupyter nbconvert --execute 04_features.ipynb
jupyter nbconvert --execute 05_modeling.ipynb
jupyter nbconvert --execute 06_predictions.ipynb
```

### ✅ Évolution & Maintenance

**Ajout nouvelle source** :
1. Télécharger dans Bronze (01_download)
2. Parser/nettoyer dans Silver (03_etl)
3. Joindre dans Gold (04_features)

**Modification transformation** :
- Changer code Silver → Re-run 03_etl → Silver régénéré
- Bronze non impacté (immuable)
- Gold automatiquement mis à jour au prochain run

---

## Accès aux Données dans Notebooks

### Import Configuration

```python
# En début de chaque notebook (après imports pandas/numpy)
import sys
sys.path.append('..')
from config import DATA_BRONZE, DATA_SILVER, DATA_GOLD

# Vérifier chemins
print(f"🥉 Bronze: {DATA_BRONZE}")
print(f"🥈 Silver: {DATA_SILVER}")
print(f"🥇 Gold: {DATA_GOLD}")
```

### Lecture Bronze (CSV)

```python
import pandas as pd

# Lecture CSV avec parsing correct
df_elections = pd.read_csv(
    DATA_BRONZE / "elections_agregees_1999_2024.csv",
    sep=";",  # Séparateur point-virgule
    dtype={'code_commune': str, 'code_departement': str},  # Types explicites
    chunksize=10000  # Lecture par blocs si volumineux
)

# Lecture Excel INSEE avec skiprows
df_population = pd.read_excel(
    DATA_BRONZE / "population_historique_1968_2022/pop-16ans-dipl6822.xlsx",
    engine='openpyxl',
    skiprows=5  # Sauter métadonnées INSEE
)
```

### Écriture Silver (Parquet)

```python
# Conversion CSV → Parquet optimisé
df_elections_clean.to_parquet(
    DATA_SILVER / "elections_petite_couronne.parquet",
    engine='pyarrow',
    compression='snappy',
    index=False
)

print(f"✅ Silver créé : {DATA_SILVER / 'elections_petite_couronne.parquet'}")
```

### Lecture Silver (Parquet)

```python
# Lecture Parquet ultra-rapide
df = pd.read_parquet(DATA_SILVER / "elections_petite_couronne.parquet")

# Lecture colonnes spécifiques (performance)
df_subset = pd.read_parquet(
    DATA_SILVER / "elections_petite_couronne.parquet",
    columns=['code_commune', 'annee', 'voix', 'nuance']
)
```

### Écriture Gold (Résultats ML)

```python
# Export prédictions
df_predictions.to_parquet(
    DATA_GOLD / "predictions_2027.parquet",
    compression="snappy"
)

# Export métriques JSON
import json
metrics = {
    'model': 'RandomForest',
    'date': '2026-02-13',
    'rmse': 0.082,
    'r2': 0.76
}
with open(DATA_GOLD / "metriques_modele.json", 'w') as f:
    json.dump(metrics, f, indent=2)

# Export CSV client
df_predictions.to_csv(
    DATA_GOLD / "export_client_2027.csv",
    index=False,
    encoding='utf-8'
)
```

---

## Tests Qualité Données

### Silver Layer - Data Quality Checks

```python
def validate_silver_quality(df, name):
    """Tests qualité obligatoires couche Silver"""
    print(f"\n🔍 Validation qualité : {name}")
    
    issues = []
    
    # Test 1: Valeurs manquantes < 5%
    missing_pct = (df.isnull().sum() / len(df)) * 100
    high_missing = missing_pct[missing_pct > 5]
    if len(high_missing) > 0:
        issues.append(f"❌ Colonnes avec >5% manquants: {list(high_missing.index)}")
    else:
        print("✅ Valeurs manquantes OK (< 5% par colonne)")
    
    # Test 2: Pas de doublons sur clé primaire
    if 'code_commune' in df.columns:
        duplicates = df['code_commune'].duplicated().sum()
        if duplicates > 0:
            issues.append(f"❌ {duplicates} doublons sur code_commune")
        else:
            print("✅ Pas de doublons sur code_commune")
    
    # Test 3: Types cohérents
    expected_types = {
        'code_commune': 'object',  # string
        'population': 'int64',
        'revenus_median': 'float64'
    }
    for col, expected_type in expected_types.items():
        if col in df.columns and df[col].dtype != expected_type:
            issues.append(f"❌ {col}: type {df[col].dtype} != attendu {expected_type}")
    
    if not issues:
        print("✅ VALIDATION RÉUSSIE")
        return True
    else:
        print("⚠️  PROBLÈMES DÉTECTÉS:")
        for issue in issues:
            print(f"  {issue}")
        return False

# Utilisation
validate_silver_quality(df_elections_clean, "elections_petite_couronne")
```

---

## Références

### Documentation Officielle

- [Databricks - Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)
- [Delta Lake - Best Practices](https://docs.delta.io/latest/best-practices.html)
- [Snowflake - Multi-Tier Data Architecture](https://www.snowflake.com/guides/multi-tier-data-architecture)
- [Azure Synapse - Lakehouse Architecture](https://learn.microsoft.com/en-us/azure/synapse-analytics/)

### Livres Recommandés

- **"Data Engineering with Python"** - Paul Crickard (O'Reilly, 2023)
- **"Designing Data-Intensive Applications"** - Martin Kleppmann (O'Reilly, 2017)
- **"The Data Warehouse Toolkit"** - Ralph Kimball (Wiley, 2013)

### Articles & Blogs

- [Databricks Blog - Delta Lake Architecture](https://www.databricks.com/blog)
- [Towards Data Science - Medallion Architecture](https://towardsdatascience.com)

---

**Document créé le** : 13 février 2026  
**Auteur** : Projet MSPR TPRE813 - EPSI 2026  
**Version** : 1.0
