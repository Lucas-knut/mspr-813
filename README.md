# MSPR Big Data - Prédiction Électorale

**Projet EPSI - BLOC 3 RNCP35584**
Machine Learning pour predire les tendances electorales (Gauche / Centre / Droite) sur ~35 000 communes de France metropolitaine pour 2022, avec comparaison aux resultats reels 2022. L'extreme droite (FN, RN, etc.) est fusionnee dans le bloc Droite.

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

Acces :
- JupyterLab : http://localhost:8888
- pgAdmin    : http://localhost:5050  (admin@epsi.fr / admin)
- Metabase   : http://localhost:3000

### Initialiser la base de données

Dans pgAdmin ou via psql, exécuter dans l'ordre :

```sql
-- Schémas Petite Couronne
\i scripts/init_db.sql

-- Schémas France métropolitaine
\i scripts/init_db_france.sql
```

### Données Bronze

Toutes les données sont téléchargées automatiquement par le notebook :

```
notebooks/communes/01_data_download.ipynb
```

---

## Pipeline d'exécution

### Exploration / EDA (optionnel)

| Notebook | Rôle |
|----------|------|
| `notebooks/communes/01_data_download.ipynb` | Téléchargement toutes les données sources (élections, COG, démographie, économie, éducation) |
| `notebooks/communes/02_exploration.ipynb` | Analyse exploratoire des données Bronze |

### Petite Couronne (POC — 144 communes, départements 75/92/93/94)

| Ordre | Notebook | Rôle |
|-------|----------|------|
| 1 | `notebooks/communes/petite_couronne/01_etl_bronze_to_postgres.ipynb` | ETL Bronze → `silver.*` |
| 2 | `notebooks/communes/petite_couronne/02_feature_engineering.ipynb` | Features → `gold.features_communes` |
| 3 | `notebooks/communes/petite_couronne/03_modeling.ipynb` | ML + prédictions → `gold.predictions_2022` |

### France métropolitaine (~35 000 communes)

| Ordre | Notebook | Rôle |
|-------|----------|------|
| 1 | `notebooks/communes/france/01_etl_bronze_to_postgres.ipynb` | ETL Bronze → `silver_france.*` |
| 2 | `notebooks/communes/france/02_feature_engineering.ipynb` | Features → `gold_france.features_communes` |
| 3 | `notebooks/communes/france/03_modeling.ipynb` | ML + prédictions → `gold_france.predictions_2022` |

---

## Résultats

**Strategie** : entrainement sur 2002/2007/2012, test sur 2017, prediction 2022 comparee aux resultats reels 2022.

| Perimetre | Modele retenu | Accuracy (test 2017) | Predictions |
|-----------|--------------|----------------------|-------------|
| Petite Couronne | GradientBoosting | — | ~124 communes |
| France metro | GradientBoosting | **93.3%** | 34 791 communes |

**Comparaison reel vs predit 2022 (France metropolitaine) :**

| Bloc | % communes reel 2022 | % communes predit 2022 | Ecart |
|------|---------------------|------------------------|-------|
| Droite | 75.3% | 77.8% | +2.5 |
| Centre | 14.6% | 20.6% | +6.0 |
| Gauche | 10.1% | 1.7% | -8.4 |

Note : le biais sur la Gauche est documente — les classes sont fortement desequilibrees
(~75% des exemples d'entrainement sont Droite). La Gauche est concentree dans quelques
grandes communes tres peuplees mais peu nombreuses.

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

---

## Metabase — Configuration initiale

### Prérequis

Lors de la première connexion à Metabase (http://localhost:3000), l'assistant de
configuration demande d'ajouter une base de données. Renseigner :

- **Nom : `MSPR 813`** (nom exact — le script `setup_metabase.py` en dépend)
- Type : PostgreSQL
- Host : `postgres`, Port : `5432`, Database : `mspr813`
- User : `mspr_user`, Password : `mspr_password`
- Schémas à exposer : `silver`, `silver_france`, `gold`, `gold_france`

Après connexion, synchroniser les schémas si nécessaire :
Admin > Databases > MSPR 813 > Sync database schema now.

### Création des questions et dashboards

```bash
python3 scripts/setup_metabase.py
```

Le script demande le mot de passe Metabase au lancement (jamais stocké). Il est idempotent pour les questions (skip si déjà existantes) et recrée les dashcards à chaque run.

### Dashboards créés

| Dashboard | Questions |
|-----------|-----------|
| Dashboard 1 — Vue nationale | Q1, Q2, Q3 |
| Dashboard 2 — Analyse sociodemographique | Q4, Q5, Q6, Q8 |
| Dashboard 3 — Typologie territoire | Q7, Q12, Q14 |
| Dashboard 4 — Departements cles | Q9, Q10, Q15 |
| Dashboard 5 — Predictions 2022 | Q11, Q13, Q14 |
| Dashboard 6 — Comparaison reel vs predit 2022 | Q21, Q16, Q17, Q18, Q19, Q20 |

Voir `docs/METABASE_QUESTIONS.md` pour la definition complete des 21 questions (SQL natif).
